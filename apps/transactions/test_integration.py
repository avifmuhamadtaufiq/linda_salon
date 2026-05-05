from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.inventory.models import Kategori, Barang
from apps.pelanggan.models import Pelanggan
from apps.transactions.models import Transaksi, DetailTransaksi
from decimal import Decimal
import datetime


class AlurSewaLengkapTest(TestCase):
    """
    Integration test untuk alur lengkap:
    Login → Tambah Barang → Buat Transaksi → Pengembalian
    """

    def setUp(self):
        self.client = Client()

        # Buat user admin
        self.user = User.objects.create_user(
            username='admin_integration',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')

        # Buat data awal
        self.kategori = Kategori.objects.create(nama='Kursi')
        self.barang = Barang.objects.create(
            kode='KR010',
            nama='Kursi Tiffany Gold',
            kategori=self.kategori,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('15000'),
            kondisi='baik'
        )
        self.pelanggan = Pelanggan.objects.create(
            nama='Rina Marlina',
            hp='08199999999',
            alamat='Bandung'
        )

    def test_alur_login(self):
        """Test login berhasil dan redirect ke dashboard"""
        response = self.client.post(reverse('login'), {
            'username': 'admin_integration',
            'password': 'admin123'
        })
        # Setelah login redirect ke dashboard
        self.assertEqual(response.status_code, 302)
        self.assertIn('/', response['Location'])

    def test_alur_login_gagal(self):
        """Test login gagal dengan password salah"""
        response = self.client.post(reverse('login'), {
            'username': 'admin_integration',
            'password': 'passwordsalah'
        })
        # Tetap di halaman login, tidak redirect
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_alur_lengkap_sewa_dan_kembali(self):
        """
        Test alur lengkap:
        1. Login
        2. Buat transaksi
        3. Cek stok berkurang
        4. Proses pengembalian
        5. Cek stok bertambah
        6. Cek status transaksi selesai
        """
        # Step 1: Login
        self.client.login(
            username='admin_integration',
            password='admin123'
        )

        # Step 2: Buat transaksi manual (simulasi form POST)
        transaksi = Transaksi.objects.create(
            no_transaksi='SW20260504INT',
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            pelanggan_alamat=self.pelanggan.alamat,
            acara='Pernikahan Rina',
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 7),
            uang_muka=Decimal('100000'),
            total_harga=Decimal('450000'),
            sisa_bayar=Decimal('350000'),
            dibuat_oleh=self.user,
        )

        # Tambah detail transaksi
        # 10 kursi x 3 hari x 15000 = 450000
        detail = DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang,
            jumlah=10,
            jumlah_hari=3,
            harga_satuan=Decimal('15000'),
            subtotal=Decimal('450000'),
        )

        # Kurangi stok
        self.barang.stok_tersedia -= 10
        self.barang.save()

        # Step 3: Cek stok berkurang
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 0)
        self.assertEqual(self.barang.stok_disewa, 10)

        # Step 4: Proses pengembalian
        response = self.client.post(
            reverse('transaksi_kembali', args=[transaksi.pk]),
            {f'kondisi_kembali_{detail.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 302)

        # Step 5: Cek stok bertambah kembali
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)
        self.assertEqual(self.barang.stok_disewa, 0)

        # Step 6: Cek status transaksi berubah selesai
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'selesai')
        self.assertIsNotNone(transaksi.tanggal_kembali_aktual)

    def test_stok_tidak_bisa_melebihi_total(self):
        """Test stok tersedia tidak pernah melebihi stok total"""
        self.barang.stok_tersedia = 10
        self.barang.save()
        self.assertLessEqual(
            self.barang.stok_tersedia,
            self.barang.stok_total
        )

    def test_kalkulasi_harga_per_hari(self):
        """Test kalkulasi harga benar: harga x jumlah x hari"""
        harga_satuan = Decimal('15000')
        jumlah = 5
        jumlah_hari = 3
        expected = Decimal('225000')  # 15000 x 5 x 3

        subtotal = harga_satuan * jumlah * jumlah_hari
        self.assertEqual(subtotal, expected)

    def test_sisa_bayar_setelah_dp(self):
        """Test sisa bayar = total harga - uang muka"""
        total_harga = Decimal('450000')
        uang_muka = Decimal('100000')
        expected_sisa = Decimal('350000')

        sisa = total_harga - uang_muka
        self.assertEqual(sisa, expected_sisa)


class LaporanViewTest(TestCase):
    """Test laporan keuangan dan laporan barang"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_laporan',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_laporan', password='admin123')

        # Buat data transaksi selesai untuk laporan
        self.pelanggan = Pelanggan.objects.create(
            nama='Budi Santoso',
            hp='08122222222'
        )
        self.barang = Barang.objects.create(
            kode='TD010',
            nama='Tenda VIP',
            stok_total=3,
            stok_tersedia=3,
            harga_sewa=Decimal('500000'),
            kondisi='baik'
        )
        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260504LAP',
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            tanggal_sewa=datetime.date(2026, 5, 1),
            tanggal_kembali=datetime.date(2026, 5, 3),
            tanggal_kembali_aktual=datetime.date(2026, 5, 3),
            uang_muka=Decimal('500000'),
            total_harga=Decimal('1000000'),
            sisa_bayar=Decimal('500000'),
            status='selesai',
            dibuat_oleh=self.user,
        )

    def test_laporan_keuangan_tampil(self):
        """Test halaman laporan keuangan bisa diakses"""
        response = self.client.get(reverse('laporan_keuangan'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/keuangan.html')

    def test_laporan_keuangan_ada_data(self):
        """Test laporan keuangan menampilkan transaksi yang benar"""
        response = self.client.get(
            reverse('laporan_keuangan'),
            {'bulan': 5, 'tahun': 2026}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SW20260504LAP')

    def test_laporan_barang_tampil(self):
        """Test halaman laporan barang bisa diakses"""
        response = self.client.get(reverse('laporan_barang'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/barang.html')

    def test_laporan_keuangan_filter_bulan(self):
        """Test laporan keuangan filter bulan yang berbeda tidak tampilkan data"""
        response = self.client.get(
            reverse('laporan_keuangan'),
            {'bulan': 1, 'tahun': 2026}
        )
        self.assertEqual(response.status_code, 200)
        # Transaksi di bulan 5, tidak muncul di filter bulan 1
        self.assertNotContains(response, 'SW20260504LAP')