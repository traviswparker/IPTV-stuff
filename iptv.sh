#!/bin/bash
IP='10.0.0.10'
PORT=34400

# IPTV account lists should be:
#KEY=VALUE
# ...
#URL USER PASS
# ...

# usage: ./iptv.sh <account_list>

IN=$1

if [ "$1" == "" ]
then
	cat << EOF 
usage: 
	./iptv.sh <account_list> (to check all acccounts and report usage/expiration)
	./iptv.sh <account_list> [m3u file] (to generate m3u for least used account, signal threadfin to reload)

IPTV account lists should be:

FILTER=categories to select, !pattern to excldue
STRIP=patterns to strip from channel names. ^startwith, endswith$, or anywhere if no modifier
REMOVE=patterns for channels to remove. matches anywhere.
REPLACE=replace any channels with the same name if a channel matching name+pattern exists 
 example: REPLACE=' UHD' will turn 'ABC UHD' into 'ABC', removing any channels named 'ABC', but only if 'ABC UHD' exists.
followed by a list of:
SERVER USER PASS
...
EOF
	exit
fi

rm .tmp
OIFS=$IFS
IFS=$'\n'
for e in `grep -v ^http $IN`
do
	eval export $e &> /dev/null
done
for e in `grep ^http $IN`
do
	IFS=$OIFS
	./xtream.py $e '' | tee -a .tmp
done

if [ "$2" ]
then
	OIFS=$IFS
	IFS=$'\n'
	for l in `grep Active .tmp`
	do
		IFS=$OIFS
		used=`echo $l | cut -d' ' -f5 | cut -d/ -f1`
		total=`echo $l | cut -d' ' -f5 | cut -d/ -f2`
		echo $(($total-$used))' open '$l >> .tmp
	done
	echo
	grep open .tmp | sort -r -n -k1
	echo
	./xtream.py `grep open .tmp | sort -r -n -k1 | cut -d' ' -f3-5 | head -1` $2
	curl http://$IP:$PORT/api/ -d '{"cmd":"update.m3u"}'; echo
	echo
	docker logs -fn25 threadfin 2>&1 | grep -v PMS
fi

