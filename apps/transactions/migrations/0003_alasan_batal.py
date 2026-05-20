import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0002_jumlah_hari"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="transaksi",
            name="alasan_batal",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="transaksi",
            name="dibatalkan_oleh",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="transaksi_dibatalkan",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="transaksi",
            name="dibatalkan_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
