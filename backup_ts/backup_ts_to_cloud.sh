#!/usr/bin/env bash

TODAY="$(date +'%Y_%m_%d')"

BACKUP_NAME="ts_backup_${TODAY}"
BACKUP_FOLDER="/tmp/${BACKUP_NAME}"
BACKUP_ARCHIVE="${BACKUP_FOLDER}.tar.xz"
BACKUP_PUBLIC_KEY="${1}"
MARIADB_CONTAINER_NAME="${2}"
RCLONE_REMOTE="${3}"
RCLONE_REMOTE_FOLDER="ts_backups"
ENCRYPTED_BACKUP_ARCHIVE="${BACKUP_ARCHIVE}.crypt"
REMOTE_RETENTION="5d"

echo "Creating backup folder..."
cd /tmp
mkdir "${BACKUP_FOLDER}"
echo ""

echo "Dumping TS database..."
podman exec "${MARIADB_CONTAINER_NAME}" sh -c 'exec mariadb-dump teamspeak -uroot -p"$MARIADB_ROOT_PASSWORD"' > "${BACKUP_FOLDER}/ts_db_backup_${TODAY}.sql"
echo ""

echo "Exporting TS podman volume..."
podman volume export -o "${BACKUP_FOLDER}/ts_volume_export_${TODAY}.tar" teamspeak
echo ""

echo "Zipping backup folder..."
tar -cJf "${BACKUP_ARCHIVE}" -C "${BACKUP_FOLDER}" .
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