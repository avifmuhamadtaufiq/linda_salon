from django.contrib import admin

from .models import Barang, Gudang, Kategori


@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    list_display = ["nama", "deskripsi"]


@admin.register(Barang)
class BarangAdmin(admin.ModelAdmin):
    list_display = [
        "kode",
        "nama",
        "kategori",
        "stok_total",
        "stok_tersedia",
        "harga_sewa",
        "kondisi",
    ]
    list_filter = ["kategori", "kondisi"]
    search_fields = ["kode", "nama"]


@admin.register(Gudang)
class GudangAdmin(admin.ModelAdmin):
    list_display = ["nama", "alamat", "aktif", "created_at"]
    list_filter = ["aktif"]
