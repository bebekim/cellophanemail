#!/bin/bash
set -e

# Create test database in addition to the default database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE cellophanemail_test OWNER $POSTGRES_USER;
EOSQL

echo "Created databases: cellophanemail (dev), cellophanemail_test (test)"
