from django.db import models

class Kategori(models.Model):
    nama = models.CharField(max_length=100)
    deskripsi = models.TextField(blank=True)

    def __str__(self):
        return self.nama

    class Meta:
        verbose_name = 'Kategori'
        ordering = ['nama']


class Barang(models.Model):
    KONDISI_CHOICES = [
        ('baik', 'Baik'),
        ('rusak_ringan', 'Rusak Ringan'),
        ('rusak_berat', 'Rusak Berat'),
        ('tidak_aktif', 'Tidak Aktif'),
    ]
    kode = models.CharField(max_length=50, unique=True)
    nama = models.CharField(max_length=200)
    kategori = models.ForeignKey(Kategori, on_delete=models.SET_NULL, null=True, blank=True, related_name='barang')
    deskripsi = models.TextField(blank=True)
    stok_total = models.PositiveIntegerField(default=0)
    stok_tersedia = models.PositiveIntegerField(default=0)
    harga_sewa = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    kondisi = models.CharField(max_length=20, choices=KONDISI_CHOICES, default='baik')
    foto = models.ImageField(upload_to='barang/', blank=True, null=True)
    catatan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.kode}] {self.nama}"

    @property
    def stok_disewa(self):
        return self.stok_total - self.stok_tersedia

    class Meta:
        verbose_name = 'Barang'
        ordering = ['nama']
