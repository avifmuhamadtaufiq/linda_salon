#!/usr/bin/env python
"""
Setup otomatis Linda Salon
Jalankan: python3 setup.py
"""
import os
import sys
import subprocess

def run(cmd):
    print(f"  >> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.stdout.strip():
        print(f"     {result.stdout.strip()}")
    if result.returncode != 0 and result.stderr.strip():
        print(f"  !! {result.stderr.strip()}")
    return result.returncode

def main():
    print("\n" + "="*50)
    print("  ✦ Linda Salon — Setup Awal")
    print("="*50 + "\n")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

    print("[1] Install dependensi...")
    run(f"{sys.executable} -m pip install django==4.2.* Pillow -q")

    print("\n[2] Jalankan migrasi database...")
    run(f"{sys.executable} manage.py migrate")

    print("\n[3] Membuat akun admin...")
    import django
    django.setup()

    from django.contrib.auth.models import User
    from apps.accounts.models import UserProfile

    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser(
            username='admin',
            password='admin123',
            first_name='Administrator',
            email='admin@lindasalon.com'
        )
        UserProfile.objects.create(user=user, role='admin')
        print("  >> Akun admin dibuat (username: admin, password: admin123)")
    else:
        print("  >> Akun admin sudah ada.")

    os.makedirs('media/barang', exist_ok=True)

    print("\n" + "="*50)
    print("  ✓ Setup selesai!")
    print("="*50)
    print("\n  Jalankan server  : python3 manage.py runserver")
    print("  Buka di browser  : http://127.0.0.1:8000")
    print("  Username         : admin")
    print("  Password         : admin123")
    print("\n  ⚠ Segera ganti password setelah login!\n")

if __name__ == '__main__':
    main()
