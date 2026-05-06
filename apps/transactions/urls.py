from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaksi_list, name='transaksi_list'),
    path('create/', views.transaksi_create, name='transaksi_create'),
    path('<int:pk>/', views.transaksi_detail, name='transaksi_detail'),
    path('<int:pk>/kembali/', views.transaksi_kembali, name='transaksi_kembali'),
    path('<int:pk>/batal/', views.transaksi_batal, name='transaksi_batal'),
    path('jadwal/', views.jadwal_view, name='jadwal'),
]
