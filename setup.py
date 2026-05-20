#!/usr/bin/env python
"""
Setup otomatis Linda Salon menggunakan uv.
Jalankan: uv run python setup.py
"""

import os
import subprocess
import sys


def run(cmd: str) -> int:
    print(f" >> {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and result.stderr.strip():
        print(f" !! {result.stderr.strip()}")
    return result.returncode


def main() -> None:
    print("\n" + "=" * 50)
    print(" ✦ Linda Salon — Setup Awal (uv)")
    print("=" * 50 + "\n")

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

    print("[1] Sync dependensi dengan uv...")
    run("uv sync")

    print("\n[2] Jalankan migrasi database...")
    run("uv run python manage.py migrate")

    print("\n[3] Membuat akun admin...")
    import django

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    django.setup()

    from django.contrib.auth.models import User

    from apps.accounts.models import UserProfile

    if not User.objects.filter(username="admin").exists():
        user = User.objects.create_superuser(
            username="admin",
            password="admin123",
            first_name="Administrator",
            email="admin@lindasalon.com",
        )
        UserProfile.objects.create(user=user, role="admin")
        print(" >> Akun admin dibuat (username: admin, password: admin123)")
    else:
        print(" >> Akun admin sudah ada.")

    os.makedirs("media/barang", exist_ok=True)

    print("\n" + "=" * 50)
    print(" ✓ Setup selesai!")
    print("=" * 50)
    print("\n Jalankan server : uv run python manage.py runserver")
    print(" Buka di browser : [127.0.0.1](http://127.0.0.1:8000)")
    print(" Username        : admin")
    print(" Password        : admin123")
    print("\n ⚠ Segera ganti password setelah login!\n")


if __name__ == "__main__":
    main()
