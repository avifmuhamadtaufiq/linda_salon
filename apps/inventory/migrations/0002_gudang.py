from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Gudang',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=100)),
                ('alamat', models.TextField(blank=True)),
                ('keterangan', models.TextField(blank=True)),
                ('aktif', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Gudang',
                'verbose_name_plural': 'Daftar Gudang',
                'ordering': ['nama'],
            },
        ),
        migrations.AddField(
            model_name='barang',
            name='gudang',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='barang',
                to='inventory.gudang',
                verbose_name='Gudang'
            ),
        ),
    ]