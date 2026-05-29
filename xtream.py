#!/usr/bin/python3

import requests
import json
import sys
import os
from datetime import datetime

FILTER=os.getenv('FILTER','').split(',') #categories to select, !pattern to excldue
EXCLUDE=[f[1:] for f in FILTER if f.startswith('!')] 
FILTER=[f for f in FILTER if not f.startswith('!')]
STRIP=os.getenv('STRIP','US: ,USA: ,US | ,USA | ').split(',') #text to strip from channel names
REMOVE=os.getenv('REMOVE','').split(',') #name pattern of channels to remove
UPPER=int(os.getenv('UPPER',1)) #uppercase names
try: 
    REMOVE.remove('')
except:
    pass
FORMAT=os.getenv('FORMAT','ts') #stream format

URL, USER, PASS = sys.argv[1:4]
try:
    M3U=sys.argv[4]
except:
    M3U=URL.split('/')[2].split('.')[0]+'.m3u'

def request(action):
    r=requests.get(URL+'/player_api.php',params={'username':USER,'password':PASS,'action':action})
    print (action,r.status_code, file=sys.stderr)
    r.raise_for_status()
    return json.loads(r.text)

info=request('server_info')
try:
    server_info,user_info=info['server_info'],info['user_info']
    print('%s %s %s %s %s/%s %s' % (
        URL,USER,PASS,
        user_info['status'],
        user_info['active_cons'],
        user_info['max_connections'],
        datetime.fromtimestamp(int(user_info['exp_date'])) if user_info['exp_date'] else None
        ))
except:
    sys.exit(1)

if M3U: #only checking active/expires
    cats=dict( (e['category_id'],e['category_name']) for e in request('get_live_categories') \
            if any (e['category_name'].startswith(f) for f in FILTER) \
            and not any (e['category_name'].startswith(f) for f in EXCLUDE) )
    print(sorted(cats.values()))
    streams=[s for s in request('get_live_streams') if s['category_id'] in cats and not any(r in s['name'] for r in REMOVE)]
    with open(M3U,'w') as m3u:
        print('#EXTM3U',file=m3u)
        for s in streams:
            for p in STRIP:
                s['name']=s['name'].replace(p,'')
            if UPPER: s['name']=s['name'].upper()
            s['name']=s['name'].replace(',','') #plex does not like commas
            print('#EXTINF:-1 group-title="%s" tvg-id="%s" tvg-name="%s" tvg-logo="%s",%s' % (
                cats[s['category_id']], 
                s['epg_channel_id'], 
                s['name'], 
                s['stream_icon'], 
                s['name']
                ), file=m3u)
            print('http://%s:%s/live/%s/%s/%s.%s' % (
                server_info['url'].replace('http://',''),
                server_info['port'],
                USER, PASS, s['stream_id'], FORMAT 
                ), file=m3u)

    print(M3U,len(streams))
    print('xmltv %s/xmltv.php?username=%s&password=%s' % (URL,USER,PASS))
