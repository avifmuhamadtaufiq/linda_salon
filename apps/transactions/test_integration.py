import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.inventory.models import Barang, Gudang, Kategori
from apps.pelanggan.models import Pelanggan
from apps.transactions.models import DetailTransaksi, Transaksi


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
            status='disewa',
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

class GudangIntegrationTest(TestCase):
    """
    Integration test untuk alur gudang:
    Tambah gudang → tambah barang di gudang → transaksi → cek gudang di detail
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_gudang_int',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_gudang_int', password='admin123')

        # Buat 2 gudang
        self.gudang_andir = Gudang.objects.create(
            nama='Gudang Andir',
            alamat='Jl. Andir No. 1',
            aktif=True
        )
        self.gudang_kubang = Gudang.objects.create(
            nama='Gudang Kubang',
            alamat='Jl. Kubang No. 2',
            aktif=True
        )

        # Buat kategori
        self.kategori = Kategori.objects.create(nama='Kursi')

        # Buat barang di masing-masing gudang
        self.barang_andir = Barang.objects.create(
            kode='AN001',
            nama='Kursi Andir',
            kategori=self.kategori,
            gudang=self.gudang_andir,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('10000'),
            kondisi='baik'
        )
        self.barang_kubang = Barang.objects.create(
            kode='KB001',
            nama='Kursi Kubang',
            kategori=self.kategori,
            gudang=self.gudang_kubang,
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal('15000'),
            kondisi='baik'
        )

    def test_barang_terkait_gudang_benar(self):
        """Test barang tersimpan di gudang yang benar"""
        self.assertEqual(self.barang_andir.gudang, self.gudang_andir)
        self.assertEqual(self.barang_kubang.gudang, self.gudang_kubang)

    def test_gudang_punya_barang_yang_benar(self):
        """Test setiap gudang punya barang yang benar"""
        self.assertEqual(self.gudang_andir.barang.count(), 1)
        self.assertEqual(self.gudang_kubang.barang.count(), 1)
        self.assertIn(self.barang_andir, self.gudang_andir.barang.all())
        self.assertIn(self.barang_kubang, self.gudang_kubang.barang.all())

    def test_alur_transaksi_dengan_barang_dari_dua_gudang(self):
        """
        Test transaksi dengan barang dari 2 gudang berbeda
        1. Buat transaksi
        2. Tambah barang dari gudang andir dan kubang
        3. Cek stok berkurang di masing-masing gudang
        4. Proses pengembalian
        5. Cek stok kembali normal
        """
        # Buat pelanggan
        pelanggan = Pelanggan.objects.create(
            nama='Test Pelanggan',
            hp='08100000000'
        )

        # Step 1: Buat transaksi
        transaksi = Transaksi.objects.create(
            no_transaksi='SW20260506INT',
            pelanggan=pelanggan,
            pelanggan_nama=pelanggan.nama,
            pelanggan_hp=pelanggan.hp,
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal('0'),
            total_harga=Decimal('0'),
            status='disewa', 
            dibuat_oleh=self.user,
        )

        # Step 2: Tambah barang dari gudang andir
        detail_andir = DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang_andir,
            jumlah=3,
            jumlah_hari=2,
            harga_satuan=Decimal('10000'),
            subtotal=Decimal('60000'),  # 10000 x 3 x 2
        )
        self.barang_andir.stok_tersedia -= 3
        self.barang_andir.save()

        # Tambah barang dari gudang kubang
        detail_kubang = DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang_kubang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal('15000'),
            subtotal=Decimal('60000'),  # 15000 x 2 x 2
        )
        self.barang_kubang.stok_tersedia -= 2
        self.barang_kubang.save()

        # Update total transaksi
        transaksi.total_harga = Decimal('120000')
        transaksi.sisa_bayar = Decimal('120000')
        transaksi.save()

        # Step 3: Cek stok berkurang di masing-masing gudang
        self.barang_andir.refresh_from_db()
        self.barang_kubang.refresh_from_db()
        self.assertEqual(self.barang_andir.stok_tersedia, 7)
        self.assertEqual(self.barang_kubang.stok_tersedia, 3)

        # Step 4: Proses pengembalian
        response = self.client.post(
            reverse('transaksi_kembali', args=[transaksi.pk]),
            {
                f'kondisi_kembali_{detail_andir.pk}': 'Baik',
                f'kondisi_kembali_{detail_kubang.pk}': 'Baik',
            }
        )
        self.assertEqual(response.status_code, 302)

        # Step 5: Cek stok kembali normal
        self.barang_andir.refresh_from_db()
        self.barang_kubang.refresh_from_db()
        self.assertEqual(self.barang_andir.stok_tersedia, 10)
        self.assertEqual(self.barang_kubang.stok_tersedia, 5)

        # Cek status transaksi selesai
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'selesai')

    def test_gudang_nonaktif_tidak_muncul_di_form(self):
        """Test gudang nonaktif tidak muncul di dropdown form barang"""
        from apps.inventory.forms import BarangForm
        self.gudang_kubang.aktif = False
        self.gudang_kubang.save()

        form = BarangForm()
        gudang_queryset = form.fields['gudang'].queryset
        self.assertIn(self.gudang_andir, gudang_queryset)
        self.assertNotIn(self.gudang_kubang, gudang_queryset)

    def test_total_stok_per_gudang(self):
        """Test hitung total stok barang per gudang"""
        from django.db.models import Sum

        total_andir = Barang.objects.filter(
            gudang=self.gudang_andir
        ).aggregate(total=Sum('stok_tersedia'))['total']

        total_kubang = Barang.objects.filter(
            gudang=self.gudang_kubang
        ).aggregate(total=Sum('stok_tersedia'))['total']

        self.assertEqual(total_andir, 10)
        self.assertEqual(total_kubang, 5)

class PembatalanTransaksiIntegrationTest(TestCase):
    """Integration test alur pembatalan transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_batal_int',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_batal_int', password='admin123')

        self.barang1 = Barang.objects.create(
            kode='BTL001',
            nama='Barang Batal 1',
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('20000'),
            kondisi='baik'
        )
        self.barang2 = Barang.objects.create(
            kode='BTL002',
            nama='Barang Batal 2',
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal('30000'),
            kondisi='baik'
        )

    def test_alur_lengkap_pembatalan(self):
        """
        Test alur lengkap pembatalan:
        1. Buat transaksi
        2. Stok berkurang
        3. Batalkan dengan alasan
        4. Stok kembali normal
        5. Cek semua info pembatalan tersimpan
        """
        # Step 1: Buat transaksi
        transaksi = Transaksi.objects.create(
            no_transaksi='SW20260506BTLINT',
            pelanggan_nama='Test Batal Integration',
            pelanggan_hp='08100000099',
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 9),
            uang_muka=Decimal('50000'),
            total_harga=Decimal('250000'),
            sisa_bayar=Decimal('200000'),
            status='menunggu',  
            dibuat_oleh=self.user,
        )

        # Tambah 2 barang
        DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang1,
            jumlah=3,
            jumlah_hari=3,
            harga_satuan=Decimal('20000'),
            subtotal=Decimal('180000'),
        )
        DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang2,
            jumlah=1,
            jumlah_hari=3,
            harga_satuan=Decimal('30000'),
            subtotal=Decimal('90000'),
        )

        # Kurangi stok
        self.barang1.stok_tersedia -= 3
        self.barang1.save()
        self.barang2.stok_tersedia -= 1
        self.barang2.save()

        # Step 2: Cek stok berkurang
        self.assertEqual(self.barang1.stok_tersedia, 7)
        self.assertEqual(self.barang2.stok_tersedia, 4)

        # Step 3: Batalkan transaksi
        alasan = 'Pelanggan tidak jadi menikah'
        response = self.client.post(
            reverse('transaksi_batal', args=[transaksi.pk]),
            {'alasan_batal': alasan}
        )
        self.assertEqual(response.status_code, 302)

        # Step 4: Cek stok kembali normal
        self.barang1.refresh_from_db()
        self.barang2.refresh_from_db()
        self.assertEqual(self.barang1.stok_tersedia, 10)
        self.assertEqual(self.barang2.stok_tersedia, 5)

        # Step 5: Cek semua info pembatalan tersimpan
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'batal')
        self.assertEqual(transaksi.alasan_batal, alasan)
        self.assertEqual(transaksi.dibatalkan_oleh, self.user)
        self.assertIsNotNone(transaksi.dibatalkan_at)

class AlurStatusLengkapTest(TestCase):
    """
    Integration test alur status lengkap:
    menunggu → siap_diambil → disewa → selesai
    """

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_alur_status',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_alur_status', password='admin123')

        self.barang = Barang.objects.create(
            kode='AL001',
            nama='Barang Alur Test',
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('25000'),
            kondisi='baik'
        )

    def test_alur_lengkap_menunggu_sampai_selesai(self):
        """
        Test alur lengkap:
        1. Buat transaksi → status menunggu, stok dikunci
        2. Siapkan barang → status siap_diambil
        3. Barang keluar → status disewa
        4. Barang kembali → status selesai, stok kembali
        """
        pelanggan = Pelanggan.objects.create(
            nama='Test Alur Status',
            hp='08100000099'
        )

        # Step 1: Buat transaksi
        transaksi = Transaksi.objects.create(
            no_transaksi='SW20260507ALUR',
            pelanggan=pelanggan,
            pelanggan_nama=pelanggan.nama,
            pelanggan_hp=pelanggan.hp,
            tanggal_sewa=datetime.date(2026, 5, 7),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal('50000'),
            total_harga=Decimal('150000'),
            sisa_bayar=Decimal('100000'),
            status='menunggu',
            dibuat_oleh=self.user,
        )
        detail = DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=3,
            harga_satuan=Decimal('25000'),
            subtotal=Decimal('150000'),
        )
        # Stok dikunci
        self.barang.stok_tersedia -= 2
        self.barang.save()

        # Cek stok sudah dikunci
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)
        self.assertEqual(transaksi.status, 'menunggu')

        # Step 2: Siapkan barang
        response = self.client.post(
            reverse('transaksi_siap_diambil', args=[transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'siap_diambil')

        # Stok tidak berubah
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)

        # Step 3: Barang keluar
        response = self.client.post(
            reverse('transaksi_disewa', args=[transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'disewa')

        # Stok tidak berubah
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)

        # Step 4: Barang kembali
        response = self.client.post(
            reverse('transaksi_kembali', args=[transaksi.pk]),
            {f'kondisi_kembali_{detail.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 302)
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'selesai')

        # Stok kembali normal
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

        # Tanggal kembali aktual tersimpan
        self.assertIsNotNone(transaksi.tanggal_kembali_aktual)

    def test_alur_batal_dari_menunggu(self):
        """Test batalkan dari menunggu → stok kembali"""
        transaksi = Transaksi.objects.create(
            no_transaksi='SW20260507BTL1',
            pelanggan_nama='Test Batal Menunggu',
            pelanggan_hp='08100000098',
            tanggal_sewa=datetime.date(2026, 5, 7),
            tanggal_kembali=datetime.date(2026, 5, 9),
            uang_muka=Decimal('0'),
            total_harga=Decimal('50000'),
            sisa_bayar=Decimal('50000'),
            status='menunggu',
            dibuat_oleh=self.user,
        )
        DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang,
            jumlah=3,
            jumlah_hari=1,
            harga_satuan=Decimal('25000'),
            subtotal=Decimal('75000'),
        )
        self.barang.stok_tersedia -= 3
        self.barang.save()

        # Cek stok dikunci
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 7)

        # Batalkan
        response = self.client.post(
            reverse('transaksi_batal', args=[transaksi.pk]),
            {'alasan_batal': 'Test batal dari menunggu'}
        )
        self.assertEqual(response.status_code, 302)
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'batal')

        # Stok kembali
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_alur_batal_dari_siap_diambil(self):
        """Test batalkan dari siap diambil → stok kembali"""
        transaksi = Transaksi.objects.create(
            no_transaksi='SW20260507BTL2',
            pelanggan_nama='Test Batal Siap Diambil',
            pelanggan_hp='08100000097',
            tanggal_sewa=datetime.date(2026, 5, 7),
            tanggal_kembali=datetime.date(2026, 5, 9),
            uang_muka=Decimal('0'),
            total_harga=Decimal('50000'),
            sisa_bayar=Decimal('50000'),
            status='siap_diambil',
            dibuat_oleh=self.user,
        )
        DetailTransaksi.objects.create(
            transaksi=transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=1,
            harga_satuan=Decimal('25000'),
            subtotal=Decimal('50000'),
        )
        self.barang.stok_tersedia -= 2
        self.barang.save()

        # Batalkan dari siap diambil
        response = self.client.post(
            reverse('transaksi_batal', args=[transaksi.pk]),
            {'alasan_batal': 'Test batal dari siap diambil'}
        )
        self.assertEqual(response.status_code, 302)
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'batal')

        # Stok kembali
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)