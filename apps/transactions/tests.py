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