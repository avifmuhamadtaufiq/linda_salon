from django.test import TestCase

from apps.pelanggan.forms import PelangganForm


class PelangganFormTest(TestCase):

    def test_form_valid(self):
        # Test form valid dengan data lengkap
        data = {
            'nama': 'Dewi Sartika',
            'hp': '08123456789',
            'alamat': 'Jl. Merdeka No. 1 Bandung',
            'email': 'dewi@email.com',
            'catatan': ''
        }
        form = PelangganForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_valid_tanpa_opsional(self):
        # Test form valid meski field opsional kosong
        data = {
            'nama': 'Dewi Sartika',
            'hp': '08123456789',
            'alamat': '',
            'email': '',
            'catatan': ''
        }
        form = PelangganForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_tanpa_nama(self):
        # Test form tidak valid kalau nama kosong
        data = {
            'nama': '',
            'hp': '08123456789',
            'alamat': '',
            'email': '',
            'catatan': ''
        }
        form = PelangganForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nama', form.errors)

    def test_form_invalid_tanpa_hp(self):
        # Test form tidak valid kalau hp kosong
        data = {
            'nama': 'Dewi Sartika',
            'hp': '',
            'alamat': '',
            'email': '',
            'catatan': ''
        }
        form = PelangganForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('hp', form.errors)

    def test_form_invalid_email_salah(self):
        # Test form tidak valid kalau format email salah
        data = {
            'nama': 'Dewi Sartika',
            'hp': '08123456789',
            'alamat': '',
            'email': 'bukan-email',
            'catatan': ''
        }
        form = PelangganForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)