#!/usr/bin/env bash

REMOTE_NAME="${1}"
SUBFOLDER="${2}"
MAX_DATE="1 week ago"

for d in $(rclone lsd "${REMOTE_NAME}:/${SUBFOLDER}" | awk '{print $2}')
do
    date=$(date -d ${d} +%s)
    retention_date=$(date -d "${MAX_DATE}" +%s)

    if [ $date -lt $retention_date ]
    then
        rclone purge "${REMOTE_NAME}:/${SUBFOLDER}/${d}"
        echo $d
    fi
done

rclone cleanup ${REMOTE_NAME}:
