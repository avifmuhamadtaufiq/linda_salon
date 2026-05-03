from django.urls import path
from . import views

urlpatterns = [
    path('', views.barang_list, name='barang_list'),
    path('create/', views.barang_create, name='barang_create'),
    path('<int:pk>/', views.barang_detail, name='barang_detail'),
    path('<int:pk>/edit/', views.barang_edit, name='barang_edit'),
    path('<int:pk>/delete/', views.barang_delete, name='barang_delete'),
    path('kategori/', views.kategori_list, name='kategori_list'),
    path('kategori/create/', views.kategori_create, name='kategori_create'),
]
