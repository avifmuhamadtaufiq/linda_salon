from django.db import models
from django.contrib.auth.models import User
from apps.inventory.models import Barang
from apps.pelanggan.models import Pelanggan


class Transaksi(models.Model):
    STATUS_CHOICES = [
        ('menunggu', 'Menunggu'),
        ('siap_diambil', 'Siap Diambil'),
        ('disewa', 'Sedang Disewa'),
        ('selesai', 'Selesai'),
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='menunggu')
    total_harga = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    uang_muka = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    diskon = models.DecimalField(
        max_digits=15, decimal_places=0, default=0,
        verbose_name='Diskon'
    )
    sisa_bayar = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    catatan = models.TextField(blank=True)
    alasan_batal = models.TextField(blank=True, null=True)
    dibatalkan_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='transaksi_dibatalkan'
    )
    dibatalkan_at = models.DateTimeField(null=True, blank=True)
    dibuat_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='transaksi'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.no_transaksi} - {self.pelanggan_nama}"

    @property
    def total_setelah_diskon(self):
        return self.total_harga - self.diskon

    @property
    def total_sudah_bayar(self):
        """Total pembayaran termasuk DP + cicilan"""
        from django.db.models import Sum
        cicilan = self.pembayaran.aggregate(
            total=Sum('jumlah')
        )['total'] or 0
        return self.uang_muka + cicilan

    @property
    def sisa_bayar_real(self):
        """Sisa bayar setelah semua pembayaran"""
        return self.total_setelah_diskon - self.total_sudah_bayar

    @property
    def sudah_lunas(self):
        """Cek apakah sudah lunas"""
        return self.sisa_bayar_real <= 0


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


class Pembayaran(models.Model):
    METODE_CHOICES = [
        ('tunai', 'Tunai'),
        ('transfer', 'Transfer Bank'),
        ('qris', 'QRIS'),
        ('lainnya', 'Lainnya'),
    ]
    transaksi = models.ForeignKey(
        Transaksi, on_delete=models.CASCADE,
        related_name='pembayaran'
    )
    jumlah = models.DecimalField(max_digits=15, decimal_places=0)
    metode = models.CharField(
        max_length=20, choices=METODE_CHOICES, default='tunai'
    )
    keterangan = models.CharField(max_length=200, blank=True)
    dicatat_oleh = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='pembayaran_dicatat'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaksi.no_transaksi} - {self.jumlah}"

    class Meta:
        verbose_name = 'Pembayaran'
        verbose_name_plural = 'Riwayat Pembayaran'
        ordering = ['created_at']