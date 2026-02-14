#!/bin/bash

CONTAINER_NAME="vms-db"
DB_USER=$DB_USER
DB_NAME=$DB_NAME

BACKUP_DIR="/home/ubuntu/backups/vms"
GDRIVE_DIR="gdrive:/Backups/VMS"

DATE=$(date +"%Y-%m-%d_%H-%M")
FILENAME="db_backup_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

echo "Dumping database to file $BACKUP_DIR/$FILENAME..."
docker exec -t $CONTAINER_NAME pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/$FILENAME

if [ -f "$BACKUP_DIR/$FILENAME" ]; then
    echo "Dump was successfully created, uploading to Google Drive..."

    rclone copy $BACKUP_DIR/$FILENAME $GDRIVE_DIR

    if [ $? -eq 0 ]; then
        echo "Upload success."
        rm $BACKUP_DIR/$FILENAME
    else
        echo "Error uploading to Google Drive!"
    fi
else
    echo "Error dumping database!"
    exit 1
fi

echo "Removing backups older then 30 days from Google Drive..."
rclone delete $GDRIVE_DIR --min-age 30d

echo "Done!"
