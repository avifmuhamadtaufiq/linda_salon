from django.contrib import admin

from .models import DetailTransaksi, Pembayaran, Transaksi


class DetailInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 0

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ['no_transaksi', 'pelanggan_nama', 'tanggal_sewa', 'tanggal_kembali', 'status', 'total_harga']
    list_filter = ['status', 'tanggal_sewa']
    search_fields = ['no_transaksi', 'pelanggan_nama']
    inlines = [DetailInline]

@admin.register(Pembayaran)
class PembayaranAdmin(admin.ModelAdmin):
    list_display = ['transaksi', 'jumlah', 'metode', 'dicatat_oleh', 'created_at']
    list_filter = ['metode']