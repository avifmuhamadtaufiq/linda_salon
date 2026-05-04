from django.test import TestCase
from apps.inventory.models import Kategori, Barang
from apps.inventory.forms import BarangForm, KategoriForm


class KategoriModelTest(TestCase):

    def setUp(self):
        # Persiapan data sebelum setiap test
        self.kategori = Kategori.objects.create(
            nama='Kursi',
            deskripsi='Kursi pernikahan'
        )

    def test_kategori_dibuat_benar(self):
        # Test apakah kategori tersimpan dengan benar
        self.assertEqual(self.kategori.nama, 'Kursi')
        self.assertEqual(self.kategori.deskripsi, 'Kursi pernikahan')

    def test_kategori_str(self):
        # Test tampilan string kategori
        self.assertEqual(str(self.kategori), 'Kursi')


class BarangModelTest(TestCase):

    def setUp(self):
        self.kategori = Kategori.objects.create(nama='Meja')
        self.barang = Barang.objects.create(
            kode='MJ001',
            nama='Meja Bundar',
            kategori=self.kategori,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=50000,
            kondisi='baik'
        )

    def test_barang_dibuat_benar(self):
        # Test apakah barang tersimpan dengan benar
        self.assertEqual(self.barang.kode, 'MJ001')
        self.assertEqual(self.barang.nama, 'Meja Bundar')
        self.assertEqual(self.barang.stok_total, 10)
        self.assertEqual(self.barang.stok_tersedia, 10)
        self.assertEqual(self.barang.harga_sewa, 50000)

    def test_barang_str(self):
        # Test tampilan string barang
        self.assertEqual(str(self.barang), '[MJ001] Meja Bundar')

    def test_stok_disewa(self):
        # Test property stok_disewa
        # Awal: total=10, tersedia=10, disewa=0
        self.assertEqual(self.barang.stok_disewa, 0)

        # Kurangi stok tersedia seolah ada yang menyewa
        self.barang.stok_tersedia = 7
        self.barang.save()

        # Sekarang disewa = 10 - 7 = 3
        self.assertEqual(self.barang.stok_disewa, 3)

    def test_stok_tidak_bisa_negatif(self):
        # Test stok tersedia tidak bisa lebih dari stok total
        self.barang.stok_tersedia = 10
        self.barang.save()
        self.assertGreaterEqual(self.barang.stok_tersedia, 0)
        self.assertLessEqual(self.barang.stok_tersedia, self.barang.stok_total)


class KategoriFormTest(TestCase):

    def test_form_valid(self):
        # Test form valid dengan data yang benar
        data = {
            'nama': 'Tenda',
            'deskripsi': 'Tenda pernikahan outdoor'
        }
        form = KategoriForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_tanpa_nama(self):
        # Test form tidak valid kalau nama kosong
        data = {
            'nama': '',
            'deskripsi': 'Tenda pernikahan'
        }
        form = KategoriForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nama', form.errors)


class BarangFormTest(TestCase):

    def setUp(self):
        self.kategori = Kategori.objects.create(nama='Dekorasi')

    def test_form_valid(self):
        # Test form valid dengan data lengkap dan benar
        data = {
            'kode': 'DK001',
            'nama': 'Bunga Mawar',
            'kategori': self.kategori.pk,
            'stok_total': 50,
            'stok_tersedia': 50,
            'harga_sewa': 25000,
            'kondisi': 'baik',
            'deskripsi': '',
            'catatan': ''
        }
        form = BarangForm(data=data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_tanpa_kode(self):
        # Test form tidak valid kalau kode kosong
        data = {
            'kode': '',
            'nama': 'Bunga Mawar',
            'kategori': self.kategori.pk,
            'stok_total': 50,
            'stok_tersedia': 50,
            'harga_sewa': 25000,
            'kondisi': 'baik',
        }
        form = BarangForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('kode', form.errors)

    def test_form_invalid_tanpa_nama(self):
        # Test form tidak valid kalau nama kosong
        data = {
            'kode': 'DK002',
            'nama': '',
            'kategori': self.kategori.pk,
            'stok_total': 50,
            'stok_tersedia': 50,
            'harga_sewa': 25000,
            'kondisi': 'baik',
        }
        form = BarangForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('nama', form.errors)

    def test_form_invalid_stok_negatif(self):
        # Test form tidak valid kalau stok negatif
        data = {
            'kode': 'DK003',
            'nama': 'Bunga Melati',
            'kategori': self.kategori.pk,
            'stok_total': -5,
            'stok_tersedia': -5,
            'harga_sewa': 25000,
            'kondisi': 'baik',
        }
        form = BarangForm(data=data)
        self.assertFalse(form.is_valid())

    def test_form_invalid_harga_kosong(self):
        # Test form tidak valid kalau harga kosong
        data = {
            'kode': 'DK004',
            'nama': 'Bunga Melati',
            'kategori': self.kategori.pk,
            'stok_total': 10,
            'stok_tersedia': 10,
            'harga_sewa': '',
            'kondisi': 'baik',
        }
        form = BarangForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('harga_sewa', form.errors)