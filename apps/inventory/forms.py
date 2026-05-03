from django import forms
from .models import Barang, Kategori


class BarangForm(forms.ModelForm):
    class Meta:
        model = Barang
        fields = ['kode', 'nama', 'kategori', 'deskripsi', 'stok_total', 'stok_tersedia',
                  'harga_sewa', 'kondisi', 'foto', 'catatan']
        widgets = {
            'kode': forms.TextInput(attrs={'class': 'form-control'}),
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'stok_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'stok_tersedia': forms.NumberInput(attrs={'class': 'form-control'}),
            'harga_sewa': forms.NumberInput(attrs={'class': 'form-control'}),
            'kondisi': forms.Select(attrs={'class': 'form-select'}),
            'catatan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class KategoriForm(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ['nama', 'deskripsi']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'deskripsi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
