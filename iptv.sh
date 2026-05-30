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

FILTER=category to select,!category to exclude,... 
STRIP=pattern to strip from channel names,... 
REMOVE=pattern of channels to remove,... 

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
	eval export _=_ $e
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
	grep open .tmp | sort -r -n -k1
	./xtream.py `grep open .tmp | sort -r -n -k1| cut -d' ' -f3-5 | head -1` $2
	curl http://$IP:$PORT/api/ -d '{"cmd":"update.m3u"}'; echo
	sudo docker logs -fn25 threadfin 2>&1 | grep -v PMS
fi