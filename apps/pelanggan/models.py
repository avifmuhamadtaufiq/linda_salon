from django.db import models

from apps.transactions.models import Transaksi


class Pelanggan(models.Model):
    nama = models.CharField(max_length=200)
    hp = models.CharField(max_length=20)
    alamat = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    catatan = models.TextField(blank=True)
    total_transaksi = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    transaksi_set: models.Manager[Transaksi]

    def __str__(self) -> str:
        return f"{self.nama} ({self.hp})"

    class Meta:
        verbose_name = "Pelanggan"
        ordering = ["nama"]
