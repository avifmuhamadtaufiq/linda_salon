from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaksi_list, name='transaksi_list'),
    path('create/', views.transaksi_create, name='transaksi_create'),
    path('<int:pk>/', views.transaksi_detail, name='transaksi_detail'),
    path('<int:pk>/siap-diambil/', views.transaksi_siap_diambil, name='transaksi_siap_diambil'),
    path('<int:pk>/disewa/', views.transaksi_disewa, name='transaksi_disewa'),
    path('<int:pk>/kembali/', views.transaksi_kembali, name='transaksi_kembali'),
    path('<int:pk>/batal/', views.transaksi_batal, name='transaksi_batal'),
    path('jadwal/', views.jadwal_view, name='jadwal'),
    path('<int:pk>/print-persiapan/', views.transaksi_print_persiapan, name='transaksi_print_persiapan'),
]