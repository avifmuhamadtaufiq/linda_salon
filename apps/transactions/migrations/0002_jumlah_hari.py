from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='detailtransaksi',
            name='jumlah_hari',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
