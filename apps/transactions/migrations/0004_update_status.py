from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_alasan_batal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transaksi',
            name='status',
            field=models.CharField(
                choices=[
                    ('menunggu', 'Menunggu'),
                    ('siap_diambil', 'Siap Diambil'),
                    ('disewa', 'Sedang Disewa'),
                    ('selesai', 'Selesai'),
                    ('batal', 'Dibatalkan'),
                ],
                default='menunggu',
                max_length=20
            ),
        ),
    ]