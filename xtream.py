#!/usr/bin/python3

import requests
import json
import sys
import os
from datetime import datetime

#uppercase all names
UPPER=int(os.getenv('UPPER',1)) 
#stream format
FORMAT=os.getenv('FORMAT','ts') 
# filter to these categories 
FILTER=os.getenv('FILTER','').split(',') #categories to select, !pattern to excldue
EXCLUDE=[f[1:] for f in FILTER if f.startswith('!')] 
FILTER=[f for f in FILTER if not f.startswith('!')]
# patterns to strip from channel names. ^startwith, endswith$, or anywhere if no modifier
STRIP=os.getenv('STRIP','^US: ,^USA: ,^US | ,^USA | ').split(',')
# pattern of channels to remove. matches anywhere.
REMOVE=os.getenv('REMOVE','').split(',')
try: 
    REMOVE.remove('')
except:
    pass
# replace any channels with the same name if a channel matching name+pattern exists 
# example: REPLACE=' UHD' will turn 'ABC UHD' into 'ABC', removing any channels named 'ABC', but only if 'ABC UHD' exists.
REPLACE=os.getenv('REPLACE','').split(',')
try: 
    REPLACE.remove('')
except:
    pass

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
    print('categories',len(cats))
    streams=[s for s in request('get_live_streams') if s['category_id'] in cats]
    print('streams',len(streams))
    with open(M3U,'w') as m3u:
        out=[]
        skip=[]
        print('#EXTM3U',file=m3u)
        for s in streams:
            n=s['name'].upper() if UPPER else s['name']
            if  any(r in n for r in REMOVE):
                continue
            for p in STRIP:
                if p.startswith('^'):
                    if n.startswith(p[1:]):
                        n=n[len(p[1:]):]
                elif p.endswith('$'):
                    if n.endswith(p[:-1]):
                        n=n[:-len(p[:-1])]
                else: n=n.replace(p,'')
            n=n.replace(',','') #plex does not like commas
            out.append([n,
                cats[s['category_id']], 
                s['epg_channel_id'],
                s['stream_icon'], 
                s['stream_id']
                ])
        for r in REPLACE:
            skip.extend([s[0][:-len(r)] for s in out if s[0].endswith(r)])
        i=0
        for s in out:
            if s[0] not in skip:
                for r in REPLACE:
                    if s[0].endswith(r):
                        o=s[0]
                        s[0]=s[0][:-len(r)]
                print('#EXTINF:-1 group-title="%s" tvg-id="%s" tvg-name="%s" tvg-logo="%s",%s' % (s[1],s[2],s[0],s[3],s[0]), file=m3u)
                print('http://%s:%s/live/%s/%s/%s.%s' % (
                    server_info['url'].replace('hqttp://',''),
                    server_info['port'],
                    USER, PASS, s[4], FORMAT 
                    ), file=m3u)
                i+=1
    print(M3U,i)
    print('xmltv %s/xmltv.php?username=%s&password=%s' % (URL,USER,PASS))
