#!/usr/bin/env bash

REMOTE_NAME="gdrive"

for d in $(rclone lsd ${REMOTE_NAME}:/cam | awk '{print $2}')
do
    date=$(date -d ${d} +%s)
    aWeekAgo=$(date -d "1 week ago" +%s)

    if [ $date -lt $aWeekAgo ]
    then
        rclone purge "${REMOTE_NAME}:/cam/${d}"
        echo $d
    fi
done

rclone cleanup ${REMOTE_NAME}:
