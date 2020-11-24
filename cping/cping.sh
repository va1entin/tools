#!/usr/bin/env bash
#Usage:
#conping <port> <address>

online=0
port=$1
address=$2
echo "$(date +"%Y-%m-%d %H:%M:%S") Started pinging"
while [ $online -ne 1 ]
  do

  answer=$(nmap $address -PN -p $port | grep open)

  if [[ $answer = *"open"* ]]
  then echo "$(date +"%Y-%m-%d %H:%M:%S") Port $port on $address is reachable now."
  online=1
  fi

  sleep 1

done
