from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_update_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaksi',
            name='diskon',
            field=models.DecimalField(
                decimal_places=0, default=0,
                max_digits=15, verbose_name='Diskon'
            ),
        ),
    ]