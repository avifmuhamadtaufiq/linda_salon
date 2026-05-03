from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Kategori',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=100)),
                ('deskripsi', models.TextField(blank=True)),
            ],
            options={'verbose_name': 'Kategori', 'ordering': ['nama']},
        ),
        migrations.CreateModel(
            name='Barang',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kode', models.CharField(max_length=50, unique=True)),
                ('nama', models.CharField(max_length=200)),
                ('deskripsi', models.TextField(blank=True)),
                ('stok_total', models.PositiveIntegerField(default=0)),
                ('stok_tersedia', models.PositiveIntegerField(default=0)),
                ('harga_sewa', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('kondisi', models.CharField(choices=[('baik', 'Baik'), ('rusak_ringan', 'Rusak Ringan'), ('rusak_berat', 'Rusak Berat'), ('tidak_aktif', 'Tidak Aktif')], default='baik', max_length=20)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='barang/')),
                ('catatan', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('kategori', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='barang', to='inventory.kategori')),
            ],
            options={'verbose_name': 'Barang', 'ordering': ['nama']},
        ),
    ]
