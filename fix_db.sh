#!/bin/bash
# Fix Postgres Permissions
# Must be run as root
echo "Fixing Permissions for 'kajalborad' on 'test_db'..."

# Grant all privileges on the table
sudo -u postgres psql -d test_db -c "GRANT ALL PRIVILEGES ON TABLE lead TO kajalborad;"

# Grant permissions on the sequence (fixes ID auto-increment insert errors)
sudo -u postgres psql -d test_db -c "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO kajalborad;"

echo "Permissions Fixed."
