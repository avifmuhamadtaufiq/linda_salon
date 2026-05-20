from django.urls import path

from . import views

urlpatterns = [
    path("keuangan/", views.laporan_keuangan, name="laporan_keuangan"),
    path("barang/", views.laporan_barang, name="laporan_barang"),
]
