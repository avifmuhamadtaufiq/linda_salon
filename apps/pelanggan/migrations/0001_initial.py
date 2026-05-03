from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Pelanggan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama', models.CharField(max_length=200)),
                ('hp', models.CharField(max_length=20)),
                ('alamat', models.TextField(blank=True)),
                ('email', models.EmailField(blank=True, max_length=254)),
                ('catatan', models.TextField(blank=True)),
                ('total_transaksi', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'verbose_name': 'Pelanggan', 'ordering': ['nama']},
        ),
    ]
