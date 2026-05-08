from django.test import TestCase
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.inventory.models import Kategori, Barang
from apps.pelanggan.models import Pelanggan
from apps.transactions.models import Transaksi, DetailTransaksi
from django.test import Client
from django.urls import reverse
from decimal import Decimal
import datetime


class TransaksiModelTest(TestCase):

    def setUp(self):
        # Buat user untuk test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user, role='admin')

        # Buat pelanggan
        self.pelanggan = Pelanggan.objects.create(
            nama='Siti Rahayu',
            hp='08123456789',
            alamat='Bandung'
        )

        # Buat barang
        self.kategori = Kategori.objects.create(nama='Kursi')
        self.barang = Barang.objects.create(
            kode='KR001',
            nama='Kursi Tiffany',
            kategori=self.kategori,
            stok_total=20,
            stok_tersedia=20,
            harga_sewa=Decimal('10000'),
            kondisi='baik'
        )

        # Buat transaksi
        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260504001',
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            pelanggan_alamat=self.pelanggan.alamat,
            acara='Pernikahan Siti',
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 7),
            uang_muka=Decimal('50000'),
            total_harga=Decimal('0'),
            dibuat_oleh=self.user,
        )

    def test_transaksi_dibuat_benar(self):
        # Test apakah transaksi tersimpan dengan benar
        self.assertEqual(self.transaksi.no_transaksi, 'SW20260504001')
        self.assertEqual(self.transaksi.pelanggan_nama, 'Siti Rahayu')
        self.assertEqual(self.transaksi.status, 'menunggu')

    def test_transaksi_str(self):
        # Test tampilan string transaksi
        self.assertEqual(
            str(self.transaksi),
            'SW20260504001 - Siti Rahayu'
        )

    def test_sisa_bayar_terhitung_benar(self):
        # Test sisa bayar = total - uang muka
        self.transaksi.total_harga = Decimal('300000')
        self.transaksi.uang_muka = Decimal('50000')
        self.transaksi.sisa_bayar = (
            self.transaksi.total_harga - self.transaksi.uang_muka
        )
        self.transaksi.save()
        self.assertEqual(self.transaksi.sisa_bayar, Decimal('250000'))


class DetailTransaksiTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser2',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.user, role='admin')

        self.barang = Barang.objects.create(
            kode='KR002',
            nama='Kursi Merah',
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('15000'),
            kondisi='baik'
        )

        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260504002',
            pelanggan_nama='Budi Santoso',
            pelanggan_hp='08111111111',
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 6),
            uang_muka=Decimal('0'),
            total_harga=Decimal('0'),
            dibuat_oleh=self.user,
        )

    def test_subtotal_harga_per_hari(self):
        # Test subtotal = harga x jumlah x hari
        # 15000 x 5 kursi x 2 hari = 150000
        detail = DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=5,
            jumlah_hari=2,
            harga_satuan=Decimal('15000'),
            subtotal=Decimal('15000') * 5 * 2,
        )
        self.assertEqual(detail.subtotal, Decimal('150000'))

    def test_stok_berkurang_saat_sewa(self):
        # Test stok berkurang setelah barang disewa
        stok_awal = self.barang.stok_tersedia
        jumlah_sewa = 3

        # Simulasi pengurangan stok
        self.barang.stok_tersedia -= jumlah_sewa
        self.barang.save()

        self.assertEqual(
            self.barang.stok_tersedia,
            stok_awal - jumlah_sewa
        )

    def test_stok_bertambah_saat_kembali(self):
        # Test stok bertambah setelah barang dikembalikan
        # Simulasi stok berkurang dulu
        self.barang.stok_tersedia = 7
        self.barang.save()

        jumlah_kembali = 3

        # Simulasi pengembalian
        self.barang.stok_tersedia += jumlah_kembali
        self.barang.save()

        self.assertEqual(self.barang.stok_tersedia, 10)


class TransaksiViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_test3',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_test3', password='admin123')

        self.pelanggan = Pelanggan.objects.create(
            nama='Ani Wijaya',
            hp='08111111111'
        )
        self.barang = Barang.objects.create(
            kode='TD001',
            nama='Tenda Dekorasi',
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal('100000'),
            kondisi='baik'
        )
        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260504003',
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 6),
            uang_muka=Decimal('100000'),
            total_harga=Decimal('200000'),
            sisa_bayar=Decimal('100000'),
            status='disewa',
            dibuat_oleh=self.user,
        )

    def test_transaksi_list_tampil(self):
        # Test halaman daftar transaksi bisa diakses
        response = self.client.get(reverse('transaksi_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaksi_list.html')

    def test_transaksi_list_ada_data(self):
        # Test daftar transaksi menampilkan data yang benar
        response = self.client.get(reverse('transaksi_list'))
        self.assertContains(response, 'SW20260504003')

    def test_transaksi_detail_tampil(self):
        # Test halaman detail transaksi bisa diakses
        response = self.client.get(
            reverse('transaksi_detail', args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SW20260504003')

    def test_transaksi_create_GET(self):
        # Test halaman form buat transaksi bisa diakses
        response = self.client.get(reverse('transaksi_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/transaksi_form.html')

    def test_transaksi_kembali(self):
        # Test proses pengembalian barang
        # Tambah detail dulu
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal('100000'),
            subtotal=Decimal('400000'),
        )
        self.barang.stok_tersedia = 3
        self.barang.save()

        # Proses pengembalian
        response = self.client.post(
            reverse('transaksi_kembali', args=[self.transaksi.pk]),
            {f'kondisi_kembali_{DetailTransaksi.objects.first().pk}': 'Baik'}
        )

        # Cek redirect setelah berhasil
        self.assertEqual(response.status_code, 302)

        # Cek status transaksi berubah jadi selesai
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'selesai')

        # Cek stok bertambah kembali
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 5)

    def test_jadwal_tampil(self):
        # Test halaman jadwal bisa diakses
        response = self.client.get(reverse('jadwal'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'transactions/jadwal.html')

    def test_filter_by_pengguna(self):
        """Test filter transaksi berdasarkan pengguna"""

        # Buat user karyawan
        karyawan = User.objects.create_user(
            username='karyawan_test',
            password='karyawan123'
        )
        UserProfile.objects.create(user=karyawan, role='karyawan')

        # Buat transaksi oleh karyawan
        Transaksi.objects.create(
            no_transaksi='SW20260504KRY',
            pelanggan_nama='Pelanggan Karyawan',
            pelanggan_hp='08133333333',
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 6),
            uang_muka=Decimal('0'),
            total_harga=Decimal('100000'),
            sisa_bayar=Decimal('100000'),
            dibuat_oleh=karyawan,
        )

        # Filter by admin → hanya tampil transaksi admin
        response = self.client.get(
            reverse('transaksi_list'),
            {'pengguna': self.user.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'SW20260504003')
        self.assertNotContains(response, 'SW20260504KRY')

        # Filter by karyawan → hanya tampil transaksi karyawan
        response = self.client.get(
            reverse('transaksi_list'),
            {'pengguna': karyawan.pk}
        )
        self.assertContains(response, 'SW20260504KRY')
        self.assertNotContains(response, 'SW20260504003')

        # Tanpa filter → semua transaksi tampil
        response = self.client.get(reverse('transaksi_list'))
        self.assertContains(response, 'SW20260504003')
        self.assertContains(response, 'SW20260504KRY')

class TransaksiBatalViewTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Buat admin
        self.admin = User.objects.create_user(
            username='admin_batal',
            password='admin123'
        )
        UserProfile.objects.create(user=self.admin, role='admin')

        # Buat karyawan
        self.karyawan = User.objects.create_user(
            username='karyawan_batal',
            password='karyawan123'
        )
        UserProfile.objects.create(user=self.karyawan, role='karyawan')

        # Buat barang
        self.barang = Barang.objects.create(
            kode='TD099',
            nama='Tenda Test Batal',
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('50000'),
            kondisi='baik'
        )

        # Buat transaksi aktif
        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260506BTL',
            pelanggan_nama='Pelanggan Batal',
            pelanggan_hp='08100000001',
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal('0'),
            total_harga=Decimal('100000'),
            sisa_bayar=Decimal('100000'),
            status='menunggu',
            dibuat_oleh=self.admin,
        )

        # Tambah detail transaksi
        self.detail = DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=1,
            harga_satuan=Decimal('50000'),
            subtotal=Decimal('100000'),
        )

        # Kurangi stok
        self.barang.stok_tersedia -= 2
        self.barang.save()

    def test_halaman_batal_tampil_admin(self):
        """Test admin bisa akses halaman batalkan transaksi"""
        self.client.login(username='admin_batal', password='admin123')
        response = self.client.get(
            reverse('transaksi_batal', args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'transactions/transaksi_batal.html'
        )

    def test_halaman_batal_tampil_karyawan(self):
        """Test karyawan bisa akses halaman batalkan transaksi miliknya sendiri"""
        # Buat transaksi milik karyawan
        transaksi_karyawan = Transaksi.objects.create(
            no_transaksi='SW20260506KRYW',
            pelanggan_nama='Pelanggan Karyawan',
            pelanggan_hp='08100000003',
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal('0'),
            total_harga=Decimal('100000'),
            sisa_bayar=Decimal('100000'),
            status='menunggu',
            dibuat_oleh=self.karyawan,  # milik karyawan
        )
        self.client.login(username='karyawan_batal', password='karyawan123')
        response = self.client.get(
            reverse('transaksi_batal', args=[transaksi_karyawan.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_batal_tanpa_alasan_gagal(self):
        """Test pembatalan gagal kalau alasan kosong"""
        self.client.login(username='admin_batal', password='admin123')
        response = self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': ''}
        )
        # Tetap di halaman form, tidak redirect
        self.assertEqual(response.status_code, 200)

        # Status transaksi tidak berubah
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'menunggu')

        # Stok tidak berubah
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)

    def test_batal_dengan_alasan_berhasil_admin(self):
        """Test admin bisa batalkan transaksi dengan alasan"""
        self.client.login(username='admin_batal', password='admin123')
        response = self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': 'Pelanggan membatalkan pesanan mendadak'}
        )
        # Redirect setelah berhasil
        self.assertEqual(response.status_code, 302)

        # Status berubah jadi batal
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'batal')

        # Alasan tersimpan
        self.assertEqual(
            self.transaksi.alasan_batal,
            'Pelanggan membatalkan pesanan mendadak'
        )

        # Dibatalkan oleh admin
        self.assertEqual(self.transaksi.dibatalkan_oleh, self.admin)

        # Stok kembali normal
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_batal_dengan_alasan_berhasil_karyawan(self):
        """Test karyawan bisa batalkan transaksi miliknya sendiri"""
        # Buat transaksi milik karyawan
        transaksi_karyawan = Transaksi.objects.create(
            no_transaksi='SW20260506KRYW2',
            pelanggan_nama='Pelanggan Karyawan 2',
            pelanggan_hp='08100000004',
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal('0'),
            total_harga=Decimal('100000'),
            sisa_bayar=Decimal('100000'),
            status='menunggu',
            dibuat_oleh=self.karyawan,  # milik karyawan
        )
        DetailTransaksi.objects.create(
            transaksi=transaksi_karyawan,
            barang=self.barang,
            jumlah=1,
            jumlah_hari=1,
            harga_satuan=Decimal('50000'),
            subtotal=Decimal('50000'),
        )

        self.client.login(username='karyawan_batal', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_batal', args=[transaksi_karyawan.pk]),
            {'alasan_batal': 'Barang tidak tersedia sesuai permintaan'}
        )
        self.assertEqual(response.status_code, 302)

        transaksi_karyawan.refresh_from_db()
        self.assertEqual(transaksi_karyawan.status, 'batal')
        self.assertEqual(transaksi_karyawan.dibatalkan_oleh, self.karyawan)

    def test_transaksi_selesai_tidak_bisa_dibatalkan(self):
        """Test transaksi yang sudah selesai tidak bisa dibatalkan"""
        self.transaksi.status = 'selesai'
        self.transaksi.save()

        self.client.login(username='admin_batal', password='admin123')
        response = self.client.get(
            reverse('transaksi_batal', args=[self.transaksi.pk])
        )
        # Harus 404 karena filter status='aktif' di view
        self.assertEqual(response.status_code, 404)

    def test_transaksi_batal_tidak_bisa_dibatalkan_lagi(self):
        """Test transaksi yang sudah batal tidak bisa dibatalkan lagi"""
        self.transaksi.status = 'batal'
        self.transaksi.save()

        self.client.login(username='admin_batal', password='admin123')
        response = self.client.get(
            reverse('transaksi_batal', args=[self.transaksi.pk])
        )
        # Harus 404
        self.assertEqual(response.status_code, 404)

    def test_dibatalkan_at_tersimpan(self):
        """Test waktu pembatalan tersimpan"""
        self.client.login(username='admin_batal', password='admin123')
        self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': 'Test waktu pembatalan'}
        )
        self.transaksi.refresh_from_db()
        self.assertIsNotNone(self.transaksi.dibatalkan_at)

class StatusTransaksiViewTest(TestCase):
    """Test alur perubahan status transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_status',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_status', password='admin123')

        self.barang = Barang.objects.create(
            kode='ST001',
            nama='Barang Status Test',
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('20000'),
            kondisi='baik'
        )

        # Transaksi awal status menunggu
        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260507ST1',
            pelanggan_nama='Test Status',
            pelanggan_hp='08100000002',
            tanggal_sewa=datetime.date(2026, 5, 7),
            tanggal_kembali=datetime.date(2026, 5, 9),
            uang_muka=Decimal('0'),
            total_harga=Decimal('80000'),
            sisa_bayar=Decimal('80000'),
            status='menunggu',
            dibuat_oleh=self.user,
        )
        self.detail = DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal('20000'),
            subtotal=Decimal('80000'),
        )
        # Stok sudah dikunci saat menunggu
        self.barang.stok_tersedia -= 2
        self.barang.save()

    def test_status_awal_adalah_menunggu(self):
        """Test transaksi baru selalu status menunggu"""
        self.assertEqual(self.transaksi.status, 'menunggu')

    def test_menunggu_ke_siap_diambil(self):
        """Test ubah status dari menunggu ke siap diambil"""
        response = self.client.post(
            reverse('transaksi_siap_diambil', args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'siap_diambil')

    def test_siap_diambil_ke_disewa(self):
        """Test ubah status dari siap diambil ke disewa"""
        self.transaksi.status = 'siap_diambil'
        self.transaksi.save()

        response = self.client.post(
            reverse('transaksi_disewa', args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'disewa')

    def test_disewa_ke_selesai(self):
        """Test ubah status dari disewa ke selesai"""
        self.transaksi.status = 'disewa'
        self.transaksi.save()

        response = self.client.post(
            reverse('transaksi_kembali', args=[self.transaksi.pk]),
            {f'kondisi_kembali_{self.detail.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'selesai')

    def test_tidak_bisa_skip_menunggu_ke_disewa(self):
        """Test tidak bisa langsung dari menunggu ke disewa"""
        # Status masih menunggu, coba akses transaksi_disewa
        response = self.client.post(
            reverse('transaksi_disewa', args=[self.transaksi.pk])
        )
        # Harus 404 karena filter status='siap_diambil'
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'menunggu')

    def test_tidak_bisa_kembali_dari_menunggu(self):
        """Test tidak bisa proses kembali dari status menunggu"""
        response = self.client.post(
            reverse('transaksi_kembali', args=[self.transaksi.pk]),
            {f'kondisi_kembali_{self.detail.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'menunggu')

    def test_tidak_bisa_kembali_dari_siap_diambil(self):
        """Test tidak bisa proses kembali dari status siap diambil"""
        self.transaksi.status = 'siap_diambil'
        self.transaksi.save()

        response = self.client.post(
            reverse('transaksi_kembali', args=[self.transaksi.pk]),
            {f'kondisi_kembali_{self.detail.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'siap_diambil')

    def test_batal_dari_menunggu(self):
        """Test bisa batalkan dari status menunggu"""
        response = self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': 'Dibatalkan dari menunggu'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'batal')

        # Stok kembali normal
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_batal_dari_siap_diambil(self):
        """Test bisa batalkan dari status siap diambil"""
        self.transaksi.status = 'siap_diambil'
        self.transaksi.save()

        response = self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': 'Dibatalkan dari siap diambil'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'batal')

        # Stok kembali normal
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_tidak_bisa_batal_dari_disewa(self):
        """Test tidak bisa batalkan dari status disewa"""
        self.transaksi.status = 'disewa'
        self.transaksi.save()

        response = self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': 'Coba batalkan dari disewa'}
        )
        # Harus 404 karena filter status__in=['menunggu', 'siap_diambil']
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, 'disewa')

    def test_tidak_bisa_batal_dari_selesai(self):
        """Test tidak bisa batalkan dari status selesai"""
        self.transaksi.status = 'selesai'
        self.transaksi.save()

        response = self.client.post(
            reverse('transaksi_batal', args=[self.transaksi.pk]),
            {'alasan_batal': 'Coba batalkan dari selesai'}
        )
        self.assertEqual(response.status_code, 404)

    def test_stok_dikunci_saat_menunggu(self):
        """Test stok sudah berkurang saat status menunggu"""
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)
        self.assertEqual(self.barang.stok_disewa, 2)

    def test_stok_kembali_saat_selesai(self):
        """Test stok kembali normal saat selesai"""
        self.transaksi.status = 'disewa'
        self.transaksi.save()

        self.client.post(
            reverse('transaksi_kembali', args=[self.transaksi.pk]),
            {f'kondisi_kembali_{self.detail.pk}': 'Baik'}
        )
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_halaman_konfirmasi_siap_diambil_tampil(self):
        """Test halaman konfirmasi siap diambil bisa diakses"""
        response = self.client.get(
            reverse('transaksi_siap_diambil', args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'transactions/transaksi_konfirmasi.html'
        )

    def test_halaman_konfirmasi_disewa_tampil(self):
        """Test halaman konfirmasi disewa bisa diakses"""
        self.transaksi.status = 'siap_diambil'
        self.transaksi.save()

        response = self.client.get(
            reverse('transaksi_disewa', args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'transactions/transaksi_konfirmasi.html'
        )

class AksesKaryawanTest(TestCase):
    """Test akses karyawan opsi 3"""

    def setUp(self):
        self.client = Client()

        # Buat admin
        self.admin = User.objects.create_user(
            username='admin_akses',
            password='admin123'
        )
        UserProfile.objects.create(user=self.admin, role='admin')

        # Buat karyawan A
        self.karyawan_a = User.objects.create_user(
            username='karyawan_a',
            password='karyawan123'
        )
        UserProfile.objects.create(user=self.karyawan_a, role='karyawan')

        # Buat karyawan B
        self.karyawan_b = User.objects.create_user(
            username='karyawan_b',
            password='karyawan123'
        )
        UserProfile.objects.create(user=self.karyawan_b, role='karyawan')

        # Buat barang
        self.barang = Barang.objects.create(
            kode='AK001',
            nama='Barang Akses Test',
            stok_total=20,
            stok_tersedia=20,
            harga_sewa=Decimal('10000'),
            kondisi='baik'
        )

        # Transaksi milik karyawan A - status menunggu
        self.transaksi_a_menunggu = Transaksi.objects.create(
            no_transaksi='SW20260508AK1',
            pelanggan_nama='Pelanggan A',
            pelanggan_hp='08100000010',
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal('0'),
            total_harga=Decimal('40000'),
            sisa_bayar=Decimal('40000'),
            status='menunggu',
            dibuat_oleh=self.karyawan_a,
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi_a_menunggu,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal('10000'),
            subtotal=Decimal('40000'),
        )
        self.barang.stok_tersedia -= 2
        self.barang.save()

        # Transaksi milik karyawan A - status siap diambil
        self.transaksi_a_siap = Transaksi.objects.create(
            no_transaksi='SW20260508AK2',
            pelanggan_nama='Pelanggan A2',
            pelanggan_hp='08100000011',
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal('0'),
            total_harga=Decimal('20000'),
            sisa_bayar=Decimal('20000'),
            status='siap_diambil',
            dibuat_oleh=self.karyawan_a,
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi_a_siap,
            barang=self.barang,
            jumlah=1,
            jumlah_hari=2,
            harga_satuan=Decimal('10000'),
            subtotal=Decimal('20000'),
        )
        self.barang.stok_tersedia -= 1
        self.barang.save()

        # Transaksi milik karyawan A - status disewa
        self.transaksi_a_disewa = Transaksi.objects.create(
            no_transaksi='SW20260508AK3',
            pelanggan_nama='Pelanggan A3',
            pelanggan_hp='08100000012',
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal('0'),
            total_harga=Decimal('20000'),
            sisa_bayar=Decimal('20000'),
            status='disewa',
            dibuat_oleh=self.karyawan_a,
        )
        self.detail_disewa = DetailTransaksi.objects.create(
            transaksi=self.transaksi_a_disewa,
            barang=self.barang,
            jumlah=1,
            jumlah_hari=2,
            harga_satuan=Decimal('10000'),
            subtotal=Decimal('20000'),
        )
        self.barang.stok_tersedia -= 1
        self.barang.save()

    # ===========================
    # TEST KARYAWAN B (bukan pembuat)
    # ===========================

    def test_karyawan_lain_tidak_bisa_siap_diambil(self):
        """Test karyawan B tidak bisa proses siap diambil transaksi karyawan A"""
        self.client.login(username='karyawan_b', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_siap_diambil',
                args=[self.transaksi_a_menunggu.pk])
        )
        # Redirect ke detail dengan pesan error
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        # Status tidak berubah
        self.assertEqual(self.transaksi_a_menunggu.status, 'menunggu')

    def test_karyawan_lain_tidak_bisa_disewa(self):
        """Test karyawan B tidak bisa proses barang keluar transaksi karyawan A"""
        self.client.login(username='karyawan_b', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_disewa',
                args=[self.transaksi_a_siap.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_siap.refresh_from_db()
        self.assertEqual(self.transaksi_a_siap.status, 'siap_diambil')

    def test_karyawan_lain_tidak_bisa_kembali(self):
        """Test karyawan B tidak bisa proses pengembalian transaksi karyawan A"""
        self.client.login(username='karyawan_b', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_kembali',
                args=[self.transaksi_a_disewa.pk]),
            {f'kondisi_kembali_{self.detail_disewa.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_disewa.refresh_from_db()
        # Status tidak berubah
        self.assertEqual(self.transaksi_a_disewa.status, 'disewa')

    def test_karyawan_lain_tidak_bisa_batal(self):
        """Test karyawan B tidak bisa batalkan transaksi karyawan A"""
        self.client.login(username='karyawan_b', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_batal',
                args=[self.transaksi_a_menunggu.pk]),
            {'alasan_batal': 'Coba batalkan transaksi orang lain'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, 'menunggu')

    def test_karyawan_lain_bisa_lihat_detail(self):
        """Test karyawan B bisa lihat detail transaksi karyawan A"""
        self.client.login(username='karyawan_b', password='karyawan123')
        response = self.client.get(
            reverse('transaksi_detail',
                args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_karyawan_lain_tidak_ada_tombol_aksi(self):
        """Test karyawan B tidak lihat tombol aksi di detail transaksi karyawan A"""
        self.client.login(username='karyawan_b', password='karyawan123')
        response = self.client.get(
            reverse('transaksi_detail',
                args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)
        # Tombol aksi tidak tampil
        self.assertNotContains(response, 'Siapkan Barang')
        self.assertNotContains(response, 'Barang Keluar')
        self.assertNotContains(response, 'Proses Pengembalian')

    def test_karyawan_sendiri_ada_tombol_aksi(self):
        """Test karyawan A lihat tombol aksi di transaksi miliknya"""
        self.client.login(username='karyawan_a', password='karyawan123')
        response = self.client.get(
            reverse('transaksi_detail',
                args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)
        # Tombol aksi tampil
        self.assertContains(response, 'Siapkan Barang')

    # ===========================
    # TEST KARYAWAN A (pembuat)
    # ===========================

    def test_karyawan_sendiri_bisa_siap_diambil(self):
        """Test karyawan A bisa proses siap diambil transaksi miliknya"""
        self.client.login(username='karyawan_a', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_siap_diambil',
                args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, 'siap_diambil')

    def test_karyawan_sendiri_bisa_disewa(self):
        """Test karyawan A bisa proses barang keluar transaksi miliknya"""
        self.client.login(username='karyawan_a', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_disewa',
                args=[self.transaksi_a_siap.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_siap.refresh_from_db()
        self.assertEqual(self.transaksi_a_siap.status, 'disewa')

    def test_karyawan_sendiri_bisa_kembali(self):
        """Test karyawan A bisa proses pengembalian transaksi miliknya"""
        self.client.login(username='karyawan_a', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_kembali',
                args=[self.transaksi_a_disewa.pk]),
            {f'kondisi_kembali_{self.detail_disewa.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_disewa.refresh_from_db()
        self.assertEqual(self.transaksi_a_disewa.status, 'selesai')

    def test_karyawan_sendiri_bisa_batal(self):
        """Test karyawan A bisa batalkan transaksi miliknya"""
        self.client.login(username='karyawan_a', password='karyawan123')
        response = self.client.post(
            reverse('transaksi_batal',
                args=[self.transaksi_a_menunggu.pk]),
            {'alasan_batal': 'Dibatalkan oleh karyawan sendiri'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, 'batal')

    # ===========================
    # TEST ADMIN (bisa semua)
    # ===========================

    def test_admin_bisa_siap_diambil_transaksi_karyawan(self):
        """Test admin bisa proses siap diambil transaksi milik karyawan"""
        self.client.login(username='admin_akses', password='admin123')
        response = self.client.post(
            reverse('transaksi_siap_diambil',
                args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, 'siap_diambil')

    def test_admin_bisa_disewa_transaksi_karyawan(self):
        """Test admin bisa proses barang keluar transaksi milik karyawan"""
        self.client.login(username='admin_akses', password='admin123')
        response = self.client.post(
            reverse('transaksi_disewa',
                args=[self.transaksi_a_siap.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_siap.refresh_from_db()
        self.assertEqual(self.transaksi_a_siap.status, 'disewa')

    def test_admin_bisa_kembali_transaksi_karyawan(self):
        """Test admin bisa proses pengembalian transaksi milik karyawan"""
        self.client.login(username='admin_akses', password='admin123')
        response = self.client.post(
            reverse('transaksi_kembali',
                args=[self.transaksi_a_disewa.pk]),
            {f'kondisi_kembali_{self.detail_disewa.pk}': 'Baik'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_disewa.refresh_from_db()
        self.assertEqual(self.transaksi_a_disewa.status, 'selesai')

    def test_admin_bisa_batal_transaksi_karyawan(self):
        """Test admin bisa batalkan transaksi milik karyawan"""
        self.client.login(username='admin_akses', password='admin123')
        response = self.client.post(
            reverse('transaksi_batal',
                args=[self.transaksi_a_menunggu.pk]),
            {'alasan_batal': 'Dibatalkan oleh admin'}
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, 'batal')

    def test_admin_ada_tombol_aksi_di_semua_transaksi(self):
        """Test admin lihat tombol aksi di semua transaksi"""
        self.client.login(username='admin_akses', password='admin123')
        response = self.client.get(
            reverse('transaksi_detail',
                args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Siapkan Barang')

class PrintPersiapanViewTest(TestCase):
    """Test fitur print persiapan barang untuk gudang"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='admin_print',
            password='admin123'
        )
        UserProfile.objects.create(user=self.user, role='admin')
        self.client.login(username='admin_print', password='admin123')

        # Buat gudang
        from apps.inventory.models import Gudang
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

        # Buat kategori dan barang
        self.kategori = Kategori.objects.create(nama='Kursi')
        self.barang_andir = Barang.objects.create(
            kode='PR001',
            nama='Kursi Andir',
            kategori=self.kategori,
            gudang=self.gudang_andir,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('10000'),
            kondisi='baik'
        )
        self.barang_kubang = Barang.objects.create(
            kode='PR002',
            nama='Kursi Kubang',
            kategori=self.kategori,
            gudang=self.gudang_kubang,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal('15000'),
            kondisi='baik'
        )
        self.barang_tanpa_gudang = Barang.objects.create(
            kode='PR003',
            nama='Kursi Tanpa Gudang',
            kategori=self.kategori,
            gudang=None,
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal('12000'),
            kondisi='baik'
        )

        # Buat pelanggan
        self.pelanggan = Pelanggan.objects.create(
            nama='Siti Aminah',
            hp='08199998888',
            alamat='Jl. Bandung No. 10'
        )

        # Buat transaksi lengkap
        self.transaksi = Transaksi.objects.create(
            no_transaksi='SW20260508PR1',
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            pelanggan_alamat=self.pelanggan.alamat,
            acara='Pernikahan Siti',
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal('100000'),
            total_harga=Decimal('350000'),
            sisa_bayar=Decimal('250000'),
            catatan='Mohon disiapkan dengan hati-hati',
            status='menunggu',
            dibuat_oleh=self.user,
        )

        # Detail barang dari 2 gudang berbeda
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang_andir,
            jumlah=5,
            jumlah_hari=2,
            harga_satuan=Decimal('10000'),
            subtotal=Decimal('100000'),
            kondisi_keluar='Baik'
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang_kubang,
            jumlah=3,
            jumlah_hari=2,
            harga_satuan=Decimal('15000'),
            subtotal=Decimal('90000'),
            kondisi_keluar='Baik'
        )

    def test_halaman_print_bisa_diakses(self):
        """Test halaman print persiapan bisa diakses"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            'transactions/transaksi_print_persiapan.html'
        )

    def test_print_tampilkan_info_pelanggan(self):
        """Test halaman print menampilkan info pelanggan"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'Siti Aminah')
        self.assertContains(response, '08199998888')
        self.assertContains(response, 'Jl. Bandung No. 10')
        self.assertContains(response, 'Pernikahan Siti')

    def test_print_tampilkan_info_transaksi(self):
        """Test halaman print menampilkan info transaksi"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'SW20260508PR1')
        self.assertContains(response, '08 Mei 2026')

    def test_print_tampilkan_nama_gudang(self):
        """Test halaman print menampilkan nama gudang"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'Gudang Andir')
        self.assertContains(response, 'Gudang Kubang')

    def test_print_tampilkan_alamat_gudang(self):
        """Test halaman print menampilkan alamat gudang"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'Jl. Andir No. 1')
        self.assertContains(response, 'Jl. Kubang No. 2')

    def test_print_tampilkan_nama_barang(self):
        """Test halaman print menampilkan nama barang"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'Kursi Andir')
        self.assertContains(response, 'Kursi Kubang')

    def test_print_tampilkan_jumlah_barang(self):
        """Test halaman print menampilkan jumlah barang"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, '5')
        self.assertContains(response, '3')

    def test_print_tidak_tampilkan_harga(self):
        """Test halaman print tidak menampilkan harga"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        # Harga tidak boleh tampil
        self.assertNotContains(response, 'Rp 10000')
        self.assertNotContains(response, 'Rp 15000')
        self.assertNotContains(response, 'Rp 350000')
        self.assertNotContains(response, 'Subtotal')
        self.assertNotContains(response, 'Total')

    def test_print_tampilkan_catatan(self):
        """Test halaman print menampilkan catatan transaksi"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'Mohon disiapkan dengan hati-hati')

    def test_print_tampilkan_kolom_checklist(self):
        """Test halaman print ada kolom checklist untuk gudang"""
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertContains(response, 'check-box')

    def test_print_bisa_diakses_karyawan(self):
        """Test karyawan juga bisa akses halaman print"""
        karyawan = User.objects.create_user(
            username='karyawan_print',
            password='karyawan123'
        )
        UserProfile.objects.create(user=karyawan, role='karyawan')
        self.client.login(username='karyawan_print', password='karyawan123')
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_print_redirect_kalau_belum_login(self):
        """Test redirect ke login kalau belum login"""
        self.client.logout()
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response['Location'])

    def test_print_transaksi_tidak_ada_404(self):
        """Test transaksi tidak ada return 404"""
        response = self.client.get(
            reverse('transaksi_print_persiapan', args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_print_barang_tanpa_gudang(self):
        """Test print tetap bisa tampil meski ada barang tanpa gudang"""
        # Tambah barang tanpa gudang ke transaksi
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang_tanpa_gudang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal('12000'),
            subtotal=Decimal('48000'),
            kondisi_keluar='Baik'
        )
        response = self.client.get(
            reverse('transaksi_print_persiapan',
                args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kursi Tanpa Gudang')