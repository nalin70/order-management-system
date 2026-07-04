import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.getcwd())

import django
from django.contrib.auth import get_user_model

if __name__ == '__main__':
    django.setup()
    User = get_user_model()
    email = 'dummyadmin@example.com'
    username = 'dummyadmin'
    password = 'Admin123!'

    admin = User.objects.filter(email=email).first()
    if admin:
        print('Admin already exists:', admin.email)
    else:
        User.objects.create_superuser(email=email, username=username, password=password, role='ADMIN')
        print('Created dummy admin:', email)
