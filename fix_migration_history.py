import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())

import django
from django.db import connection

django.setup()

with connection.cursor() as cursor:
    cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('admin', 'authentication') ORDER BY app, name")
    rows = cursor.fetchall()
    print('Before:', rows)

    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='authentication' AND name='0001_initial'")
    auth_applied = cursor.fetchone()[0] > 0
    if auth_applied:
        print('authentication 0001_initial already applied; no repair needed.')
        sys.exit(0)

    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app='admin'")
    admin_count = cursor.fetchone()[0]
    if admin_count > 0:
        print(f'Removing {admin_count} admin migration records to repair history...')
        cursor.execute("DELETE FROM django_migrations WHERE app='admin'")

    cursor.execute("SELECT app, name FROM django_migrations WHERE app IN ('admin', 'authentication') ORDER BY app, name")
    print('After cleanup:', cursor.fetchall())
    print('Repair script completed. Now run migrations:')
    print('  python manage.py migrate authentication')
    print('  python manage.py migrate admin --fake')
