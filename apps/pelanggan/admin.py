from django.contrib import admin
from .models import Pelanggan

@admin.register(Pelanggan)
class PelangganAdmin(admin.ModelAdmin):
    list_display = ['nama', 'hp', 'email', 'total_transaksi', 'created_at']
    search_fields = ['nama', 'hp', 'email']
