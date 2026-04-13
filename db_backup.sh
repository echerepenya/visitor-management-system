#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "Warning: .env file not found at $ENV_FILE"
fi

CONTAINER_NAME="vms-db"
BACKUP_DIR="/home/ubuntu/backups/vms"
GDRIVE_DIR="gdrive:/Backups/VMS"

DATE=$(date +"%Y-%m-%d_%H-%M")
FILENAME="db_backup_$DATE.sql.gz"
FILEPATH="$BACKUP_DIR/$FILENAME"

mkdir -p $BACKUP_DIR

echo "Dumping database to file $FILEPATH..."
docker exec "${CONTAINER_NAME}" pg_dump -U "${DB_USER}" "${DB_NAME}" | gzip > "$FILEPATH"
if [ "${PIPESTATUS[0]}" -ne 0 ]; then
   echo "Error dumping database!"
   rm -f "$FILEPATH"
   exit 1
fi

echo "Dump was successfully created, uploading to Google Drive..."
rclone copy "$FILEPATH" $GDRIVE_DIR

if [ $? -eq 0 ]; then
    echo "Upload success."
    # rm $FILEPATH
else
    echo "Error uploading to Google Drive!"
    exit 1
fi

echo "Removing local backups older than 7 days from production server..."
find $BACKUP_DIR -type f -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Removing backups older than 30 days from Google Drive..."
rclone delete $GDRIVE_DIR --min-age 30d

echo "Done!"
