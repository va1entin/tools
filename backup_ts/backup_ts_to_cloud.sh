#!/usr/bin/env bash

TODAY="$(date +'%Y_%m_%d')"

BACKUP_NAME="ts_backup_${TODAY}"
BACKUP_FOLDER="/tmp/${BACKUP_NAME}"
BACKUP_ARCHIVE="${BACKUP_FOLDER}.zip"
BACKUP_PUBLIC_KEY="${1}"
MARIADB_CONTAINER_NAME="${2}"
TS_DATA_FOLDER="${3}"
RCLONE_REMOTE="${4}"
PODMAN_USER="${5}"
RCLONE_REMOTE_FOLDER="ts_backups"
ENCRYPTED_BACKUP_ARCHIVE="${BACKUP_ARCHIVE}.crypt"
REMOTE_RETENTION="5d"

echo "Creating backup folder..."
cd /tmp
mkdir "${BACKUP_FOLDER}"
echo ""

echo "Dumping TS database..."
sudo -u "${PODMAN_USER}" podman exec "${MARIADB_CONTAINER_NAME}" sh -c 'exec mysqldump teamspeak -uroot -p"$MYSQL_ROOT_PASSWORD"' > "${BACKUP_FOLDER}/ts_db_backup_${TODAY}.sql"
echo ""

echo "Getting TS podman volume ID..."
TS_PODMAN_VOLUME_ID=$(sudo -u "${PODMAN_USER}" podman inspect --format '{{json .HostConfig.Binds }}' teamspeak | grep -oP '[a-f0-9]+(?=:/var/ts3server)')
echo "Found TS volume ID: ${TS_VOLUME_ID}"
echo "Getting host mountpoint for TS podman volume..."
TS_PODMAN_VOLUME_HOST_MOUNTPOINT=$(sudo -u "${PODMAN_USER}" podman volume inspect --format '{{json .Mountpoint }}' "${TS_PODMAN_VOLUME_ID}" | sed 's/"//g')
echo "Found TS volume host mountpoint: ${TS_VOLUME_MOUNTPOINT}"
echo ""

echo "Copying data from TS podman volume to backup folder..."
rsync -a "${TS_PODMAN_VOLUME_HOST_MOUNTPOINT}" "${BACKUP_FOLDER}"
echo ""

echo "Zipping backup folder..."
7z a "${BACKUP_ARCHIVE}" "${BACKUP_FOLDER}"
echo ""

echo "Encrypting backup archive..."
python3 -c 'from plasm import encrypt; encrypt.encrypt_file("'"${BACKUP_ARCHIVE}"'", "'"${BACKUP_PUBLIC_KEY}"'", remove_input_file=True)'
echo ""

echo "Copying encrypted backup archive to cloud..."
rclone copy "${ENCRYPTED_BACKUP_ARCHIVE}" "${RCLONE_REMOTE}:${RCLONE_REMOTE_FOLDER}/"
echo ""

echo "Removing old backup archives in cloud..."
rclone delete --min-age "${REMOTE_RETENTION}" "${RCLONE_REMOTE}:${RCLONE_REMOTE_FOLDER}/"
echo ""

echo "Removing backup folder..."
rm -rf "${BACKUP_FOLDER}"
echo ""

echo "Removing encrypted backup archive..."
rm "${ENCRYPTED_BACKUP_ARCHIVE}"
echo ""