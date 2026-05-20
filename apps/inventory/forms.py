from django import forms

from .models import Barang, Gudang, Kategori


class BarangForm(forms.ModelForm):
    gudang = forms.ModelChoiceField(
        queryset=Gudang.objects.filter(aktif=True),
        empty_label="-- Pilih Gudang --",
        required=True,
        error_messages={"required": "Gudang wajib dipilih."},
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Barang
        fields = [
            "kode",
            "nama",
            "kategori",
            "gudang",
            "deskripsi",
            "stok_total",
            "stok_tersedia",
            "harga_sewa",
            "kondisi",
            "foto",
            "catatan",
        ]
        widgets = {
            "kode": forms.TextInput(attrs={"class": "form-control"}),
            "nama": forms.TextInput(attrs={"class": "form-control"}),
            "kategori": forms.Select(attrs={"class": "form-select"}),
            "deskripsi": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "stok_total": forms.NumberInput(attrs={"class": "form-control"}),
            "stok_tersedia": forms.NumberInput(attrs={"class": "form-control"}),
            "harga_sewa": forms.NumberInput(attrs={"class": "form-control"}),
            "kondisi": forms.Select(attrs={"class": "form-select"}),
            "catatan": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class KategoriForm(forms.ModelForm):
    class Meta:
        model = Kategori
        fields = ["nama", "deskripsi"]
        widgets = {
            "nama": forms.TextInput(attrs={"class": "form-control"}),
            "deskripsi": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class GudangForm(forms.ModelForm):
    class Meta:
        model = Gudang
        fields = ["nama", "alamat", "keterangan", "aktif"]
        widgets = {
            "nama": forms.TextInput(attrs={"class": "form-control"}),
            "alamat": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "keterangan": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
