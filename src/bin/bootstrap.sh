#!/bin/bash

# I need a shut_down method, start method

set -x

pid=0

shut_down() {
    echo "shutting down"
    
    # Kills all python processes
    ps aux |grep python |grep -v grep | awk '{print $2}' | while read line; do kill -HUP "$line"; done
    sleep 10
	ps aux
    exit
}

trap 'shut_down' SIGKILL SIGTERM SIGHUP SIGINT EXIT

#python -m compath web --host 0.0.0.0 --port 5000 --template-folder="/opt/compath/src/compath/templates" --static-folder="/opt/compath/src/compath/static" >> /data/logs/compath.log 2>&1
python -m compath web --host 0.0.0.0 --port 5000 --connection="sqlite:////data/bio2bel.db" --template-folder="/opt/compath/src/compath/templates" --static-folder="/opt/compath/src/compath/static" >> /data/logs/compath.log 2>&1

# this script must end with a persistent foreground process
# exec a command
# wait forever
while true
do
	tail -f /data/logs/compath.log & wait ${!}
done
