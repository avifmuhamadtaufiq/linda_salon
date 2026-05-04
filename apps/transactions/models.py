from django.db import models
from django.contrib.auth.models import User
from apps.inventory.models import Barang
from apps.pelanggan.models import Pelanggan


class Transaksi(models.Model):
    STATUS_CHOICES = [
        ('aktif', 'Aktif / Sedang Disewa'),
        ('selesai', 'Selesai / Sudah Dikembalikan'),
        ('batal', 'Dibatalkan'),
    ]
    no_transaksi = models.CharField(max_length=50, unique=True)
    pelanggan = models.ForeignKey(Pelanggan, on_delete=models.SET_NULL, null=True, blank=True, related_name='transaksi_set')
    pelanggan_nama = models.CharField(max_length=200)
    pelanggan_hp = models.CharField(max_length=20)
    pelanggan_alamat = models.TextField(blank=True)
    acara = models.CharField(max_length=200, blank=True)
    tanggal_sewa = models.DateField()
    tanggal_kembali = models.DateField()
    tanggal_kembali_aktual = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aktif')
    total_harga = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    uang_muka = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    sisa_bayar = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    catatan = models.TextField(blank=True)
    dibuat_oleh = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transaksi')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.no_transaksi} - {self.pelanggan_nama}"

    class Meta:
        verbose_name = 'Transaksi'
        ordering = ['-created_at']


class DetailTransaksi(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, related_name='detail')
    barang = models.ForeignKey(Barang, on_delete=models.PROTECT, related_name='detail_transaksi')
    jumlah = models.PositiveIntegerField(default=1)
    jumlah_hari = models.PositiveIntegerField(default=1)
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=0)
    subtotal = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    kondisi_keluar = models.CharField(max_length=100, blank=True)
    kondisi_kembali = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.barang.nama} x{self.jumlah} x{self.jumlah_hari} hari"

    class Meta:
        verbose_name = 'Detail Transaksi'
