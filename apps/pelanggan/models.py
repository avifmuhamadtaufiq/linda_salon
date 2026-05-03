from django.db import models

class Pelanggan(models.Model):
    nama = models.CharField(max_length=200)
    hp = models.CharField(max_length=20)
    alamat = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    catatan = models.TextField(blank=True)
    total_transaksi = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nama} ({self.hp})"

    class Meta:
        verbose_name = 'Pelanggan'
        ordering = ['nama']
