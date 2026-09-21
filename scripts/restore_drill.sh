#!/bin/sh
# Restore only into the explicitly configured clean instance. No source mutation.
set -eu
: "${RESTORE_DATABASE_URL:?Set the clean restore target via the secret environment}"
: "${BACKUP_ENCRYPTION_KEY:?Set the backup key via the secret environment}"
exec python "$(dirname "$0")/backup_database.py" restore "$@"
