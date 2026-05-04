from django.test import TestCase
from apps.inventory.models import Kategori, Barang
from apps.inventory.forms import BarangForm, KategoriForm
from apps.accounts.models import UserProfile
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal

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


class DashboardViewTest(TestCase):

    def setUp(self):
        # Buat client untuk simulasi browser
        self.client = Client()

        # Buat user admin
        self.user = User.objects.create_user(
            username='admin_test',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')

    def test_dashboard_redirect_kalau_belum_login(self):
        # Test halaman dashboard redirect ke login kalau belum login
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_dashboard_bisa_diakses_setelah_login(self):
        # Test dashboard bisa diakses setelah login
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_pakai_template_yang_benar(self):
        # Test dashboard pakai template yang benar
        self.client.login(username='admin_test', password='admin123')
        response = self.client.get(reverse('dashboard'))
        self.assertTemplateUsed(response, 'inventory/dashboard.html')


class BarangViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_test2',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_test2', password='admin123')

        self.kategori = Kategori.objects.create(nama='Kursi')
        self.barang = Barang.objects.create(
            kode='KR001',
            nama='Kursi Tiffany',
            kategori=self.kategori,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('10000'),
            kondisi='baik'
        )

    def test_barang_list_tampil(self):
        # Test halaman daftar barang bisa diakses
        response = self.client.get(reverse('barang_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/barang_list.html')

    def test_barang_list_ada_data(self):
        # Test daftar barang menampilkan data yang benar
        response = self.client.get(reverse('barang_list'))
        self.assertContains(response, 'Kursi Tiffany')

    def test_barang_create_GET(self):
        # Test halaman form tambah barang bisa diakses
        response = self.client.get(reverse('barang_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/barang_form.html')

    def test_barang_create_POST_valid(self):
        # Test tambah barang baru dengan data valid
        data = {
            'kode': 'MJ001',
            'nama': 'Meja Bundar',
            'kategori': self.kategori.pk,
            'stok_total': 5,
            'stok_tersedia': 5,
            'harga_sewa': 50000,
            'kondisi': 'baik',
            'deskripsi': '',
            'catatan': ''
        }
        response = self.client.post(reverse('barang_create'), data)
        # Setelah berhasil redirect ke barang_list
        self.assertEqual(response.status_code, 302)
        # Pastikan barang tersimpan di database
        self.assertTrue(Barang.objects.filter(kode='MJ001').exists())

    def test_barang_create_POST_invalid(self):
        # Test tambah barang dengan data tidak valid (kode kosong)
        data = {
            'kode': '',
            'nama': 'Meja Bundar',
            'stok_total': 5,
            'stok_tersedia': 5,
            'harga_sewa': 50000,
            'kondisi': 'baik',
        }
        response = self.client.post(reverse('barang_create'), data)
        # Tidak redirect, tetap di halaman form
        self.assertEqual(response.status_code, 200)
        # Barang tidak tersimpan
        self.assertFalse(Barang.objects.filter(nama='Meja Bundar').exists())

    def test_barang_detail_tampil(self):
        # Test halaman detail barang bisa diakses
        response = self.client.get(
            reverse('barang_detail', args=[self.barang.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kursi Tiffany')

    def test_barang_delete(self):
        # Test hapus barang
        response = self.client.post(
            reverse('barang_delete', args=[self.barang.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Barang.objects.filter(pk=self.barang.pk).exists())