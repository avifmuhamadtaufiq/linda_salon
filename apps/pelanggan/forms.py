from django import forms

from .models import Pelanggan


class PelangganForm(forms.ModelForm):
    class Meta:
        model = Pelanggan
        fields = ["nama", "hp", "alamat", "email", "catatan"]
        widgets = {
            "nama": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nama lengkap pelanggan"}
            ),
            "hp": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "08xx-xxxx-xxxx"}
            ),
            "alamat": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Alamat lengkap",
                }
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "email@contoh.com"}
            ),
            "catatan": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
