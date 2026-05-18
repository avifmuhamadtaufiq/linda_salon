from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0005_diskon'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pembayaran',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True,
                    serialize=False, verbose_name='ID'
                )),
                ('jumlah', models.DecimalField(
                    decimal_places=0, max_digits=15
                )),
                ('metode', models.CharField(
                    choices=[
                        ('tunai', 'Tunai'),
                        ('transfer', 'Transfer Bank'),
                        ('qris', 'QRIS'),
                        ('lainnya', 'Lainnya'),
                    ],
                    default='tunai', max_length=20
                )),
                ('keterangan', models.CharField(
                    blank=True, max_length=200
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('dicatat_oleh', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='pembayaran_dicatat',
                    to=settings.AUTH_USER_MODEL
                )),
                ('transaksi', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pembayaran',
                    to='transactions.transaksi'
                )),
            ],
            options={
                'verbose_name': 'Pembayaran',
                'verbose_name_plural': 'Riwayat Pembayaran',
                'ordering': ['created_at'],
            },
        ),
    ]