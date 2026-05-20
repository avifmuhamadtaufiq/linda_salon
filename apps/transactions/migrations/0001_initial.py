import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("inventory", "0001_initial"),
        ("pelanggan", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Transaksi",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("no_transaksi", models.CharField(max_length=50, unique=True)),
                ("pelanggan_nama", models.CharField(max_length=200)),
                ("pelanggan_hp", models.CharField(max_length=20)),
                ("pelanggan_alamat", models.TextField(blank=True)),
                ("acara", models.CharField(blank=True, max_length=200)),
                ("tanggal_sewa", models.DateField()),
                ("tanggal_kembali", models.DateField()),
                ("tanggal_kembali_aktual", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("aktif", "Aktif / Sedang Disewa"),
                            ("selesai", "Selesai / Sudah Dikembalikan"),
                            ("batal", "Dibatalkan"),
                        ],
                        default="aktif",
                        max_length=20,
                    ),
                ),
                (
                    "total_harga",
                    models.DecimalField(decimal_places=0, default=0, max_digits=15),
                ),
                (
                    "uang_muka",
                    models.DecimalField(decimal_places=0, default=0, max_digits=15),
                ),
                (
                    "sisa_bayar",
                    models.DecimalField(decimal_places=0, default=0, max_digits=15),
                ),
                ("catatan", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "dibuat_oleh",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaksi",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "pelanggan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaksi_set",
                        to="pelanggan.pelanggan",
                    ),
                ),
            ],
            options={"verbose_name": "Transaksi", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="DetailTransaksi",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("jumlah", models.PositiveIntegerField(default=1)),
                ("harga_satuan", models.DecimalField(decimal_places=0, max_digits=12)),
                (
                    "subtotal",
                    models.DecimalField(decimal_places=0, default=0, max_digits=15),
                ),
                ("kondisi_keluar", models.CharField(blank=True, max_length=100)),
                ("kondisi_kembali", models.CharField(blank=True, max_length=100)),
                (
                    "barang",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="detail_transaksi",
                        to="inventory.barang",
                    ),
                ),
                (
                    "transaksi",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="detail",
                        to="transactions.transaksi",
                    ),
                ),
            ],
            options={"verbose_name": "Detail Transaksi"},
        ),
    ]
