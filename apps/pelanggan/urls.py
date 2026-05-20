from django.urls import path

from . import views

urlpatterns = [
    path("", views.pelanggan_list, name="pelanggan_list"),
    path("create/", views.pelanggan_create, name="pelanggan_create"),
    path("<int:pk>/", views.pelanggan_detail, name="pelanggan_detail"),
    path("<int:pk>/edit/", views.pelanggan_edit, name="pelanggan_edit"),
    path("<int:pk>/delete/", views.pelanggan_delete, name="pelanggan_delete"),
    path("api/search/", views.pelanggan_search_api, name="pelanggan_search_api"),
]
