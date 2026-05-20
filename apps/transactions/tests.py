import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.inventory.models import Barang, Kategori
from apps.pelanggan.models import Pelanggan
from apps.transactions.models import DetailTransaksi, Transaksi


class TransaksiModelTest(TestCase):
    def setUp(self):
        # Buat user untuk test
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="admin")

        # Buat pelanggan
        self.pelanggan = Pelanggan.objects.create(
            nama="Siti Rahayu", hp="08123456789", alamat="Bandung"
        )

        # Buat barang
        self.kategori = Kategori.objects.create(nama="Kursi")
        self.barang = Barang.objects.create(
            kode="KR001",
            nama="Kursi Tiffany",
            kategori=self.kategori,
            stok_total=20,
            stok_tersedia=20,
            harga_sewa=Decimal("10000"),
            kondisi="baik",
        )

        # Buat transaksi
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260504001",
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            pelanggan_alamat=self.pelanggan.alamat,
            acara="Pernikahan Siti",
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 7),
            uang_muka=Decimal("50000"),
            total_harga=Decimal("0"),
            dibuat_oleh=self.user,
        )

    def test_transaksi_dibuat_benar(self):
        # Test apakah transaksi tersimpan dengan benar
        self.assertEqual(self.transaksi.no_transaksi, "SW20260504001")
        self.assertEqual(self.transaksi.pelanggan_nama, "Siti Rahayu")
        self.assertEqual(self.transaksi.status, "menunggu")

    def test_transaksi_str(self):
        # Test tampilan string transaksi
        self.assertEqual(str(self.transaksi), "SW20260504001 - Siti Rahayu")

    def test_sisa_bayar_terhitung_benar(self):
        # Test sisa bayar = total - uang muka
        self.transaksi.total_harga = Decimal("300000")
        self.transaksi.uang_muka = Decimal("50000")
        self.transaksi.sisa_bayar = (
            self.transaksi.total_harga - self.transaksi.uang_muka
        )
        self.transaksi.save()
        self.assertEqual(self.transaksi.sisa_bayar, Decimal("250000"))


class DetailTransaksiTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser2", password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="admin")

        self.barang = Barang.objects.create(
            kode="KR002",
            nama="Kursi Merah",
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("15000"),
            kondisi="baik",
        )

        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260504002",
            pelanggan_nama="Budi Santoso",
            pelanggan_hp="08111111111",
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 6),
            uang_muka=Decimal("0"),
            total_harga=Decimal("0"),
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
            harga_satuan=Decimal("15000"),
            subtotal=Decimal("15000") * 5 * 2,
        )
        self.assertEqual(detail.subtotal, Decimal("150000"))

    def test_stok_berkurang_saat_sewa(self):
        # Test stok berkurang setelah barang disewa
        stok_awal = self.barang.stok_tersedia
        jumlah_sewa = 3

        # Simulasi pengurangan stok
        self.barang.stok_tersedia -= jumlah_sewa
        self.barang.save()

        self.assertEqual(self.barang.stok_tersedia, stok_awal - jumlah_sewa)

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
            username="admin_test3", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_test3", password="admin123")

        self.pelanggan = Pelanggan.objects.create(nama="Ani Wijaya", hp="08111111111")
        self.barang = Barang.objects.create(
            kode="TD001",
            nama="Tenda Dekorasi",
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal("100000"),
            kondisi="baik",
        )
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260504003",
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 6),
            uang_muka=Decimal("100000"),
            total_harga=Decimal("200000"),
            sisa_bayar=Decimal("100000"),
            status="disewa",
            dibuat_oleh=self.user,
        )

    def test_transaksi_list_tampil(self):
        # Test halaman daftar transaksi bisa diakses
        response = self.client.get(reverse("transaksi_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_list.html")

    def test_transaksi_list_ada_data(self):
        # Test daftar transaksi menampilkan data yang benar
        response = self.client.get(reverse("transaksi_list"))
        self.assertContains(response, "SW20260504003")

    def test_transaksi_detail_tampil(self):
        # Test halaman detail transaksi bisa diakses
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SW20260504003")

    def test_transaksi_create_GET(self):
        # Test halaman form buat transaksi bisa diakses
        response = self.client.get(reverse("transaksi_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_form.html")

    def test_transaksi_kembali(self):
        # Test proses pengembalian barang
        # Tambah detail dulu
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal("100000"),
            subtotal=Decimal("400000"),
        )
        self.barang.stok_tersedia = 3
        self.barang.save()

        # Proses pengembalian
        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi.pk]),
            {f"kondisi_kembali_{DetailTransaksi.objects.first().pk}": "Baik"},
        )

        # Cek redirect setelah berhasil
        self.assertEqual(response.status_code, 302)

        # Cek status transaksi berubah jadi selesai
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "selesai")

        # Cek stok bertambah kembali
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 5)

    def test_jadwal_tampil(self):
        # Test halaman jadwal bisa diakses
        response = self.client.get(reverse("jadwal"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/jadwal.html")

    def test_filter_by_pengguna(self):
        """Test filter transaksi berdasarkan pengguna"""

        # Buat user karyawan
        karyawan = User.objects.create_user(
            username="karyawan_test", password="karyawan123"
        )
        UserProfile.objects.create(user=karyawan, role="karyawan")

        # Buat transaksi oleh karyawan
        Transaksi.objects.create(
            no_transaksi="SW20260504KRY",
            pelanggan_nama="Pelanggan Karyawan",
            pelanggan_hp="08133333333",
            tanggal_sewa=datetime.date(2026, 5, 4),
            tanggal_kembali=datetime.date(2026, 5, 6),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            dibuat_oleh=karyawan,
        )

        # Filter by admin → hanya tampil transaksi admin
        response = self.client.get(
            reverse("transaksi_list"), {"pengguna": self.user.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SW20260504003")
        self.assertNotContains(response, "SW20260504KRY")

        # Filter by karyawan → hanya tampil transaksi karyawan
        response = self.client.get(reverse("transaksi_list"), {"pengguna": karyawan.pk})
        self.assertContains(response, "SW20260504KRY")
        self.assertNotContains(response, "SW20260504003")

        # Tanpa filter → semua transaksi tampil
        response = self.client.get(reverse("transaksi_list"))
        self.assertContains(response, "SW20260504003")
        self.assertContains(response, "SW20260504KRY")


class TransaksiBatalViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Buat admin
        self.admin = User.objects.create_user(
            username="admin_batal", password="admin123"
        )
        UserProfile.objects.create(user=self.admin, role="admin")

        # Buat karyawan
        self.karyawan = User.objects.create_user(
            username="karyawan_batal", password="karyawan123"
        )
        UserProfile.objects.create(user=self.karyawan, role="karyawan")

        # Buat barang
        self.barang = Barang.objects.create(
            kode="TD099",
            nama="Tenda Test Batal",
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("50000"),
            kondisi="baik",
        )

        # Buat transaksi aktif
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260506BTL",
            pelanggan_nama="Pelanggan Batal",
            pelanggan_hp="08100000001",
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="menunggu",
            dibuat_oleh=self.admin,
        )

        # Tambah detail transaksi
        self.detail = DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=1,
            harga_satuan=Decimal("50000"),
            subtotal=Decimal("100000"),
        )

        # Kurangi stok
        self.barang.stok_tersedia -= 2
        self.barang.save()

    def test_halaman_batal_tampil_admin(self):
        """Test admin bisa akses halaman batalkan transaksi"""
        self.client.login(username="admin_batal", password="admin123")
        response = self.client.get(reverse("transaksi_batal", args=[self.transaksi.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_batal.html")

    def test_halaman_batal_tampil_karyawan(self):
        """Test karyawan bisa akses halaman batalkan transaksi miliknya sendiri"""
        # Buat transaksi milik karyawan
        transaksi_karyawan = Transaksi.objects.create(
            no_transaksi="SW20260506KRYW",
            pelanggan_nama="Pelanggan Karyawan",
            pelanggan_hp="08100000003",
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="menunggu",
            dibuat_oleh=self.karyawan,  # milik karyawan
        )
        self.client.login(username="karyawan_batal", password="karyawan123")
        response = self.client.get(
            reverse("transaksi_batal", args=[transaksi_karyawan.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_batal_tanpa_alasan_gagal(self):
        """Test pembatalan gagal kalau alasan kosong"""
        self.client.login(username="admin_batal", password="admin123")
        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]), {"alasan_batal": ""}
        )
        # Tetap di halaman form, tidak redirect
        self.assertEqual(response.status_code, 200)

        # Status transaksi tidak berubah
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "menunggu")

        # Stok tidak berubah
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)

    def test_batal_dengan_alasan_berhasil_admin(self):
        """Test admin bisa batalkan transaksi dengan alasan"""
        self.client.login(username="admin_batal", password="admin123")
        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]),
            {"alasan_batal": "Pelanggan membatalkan pesanan mendadak"},
        )
        # Redirect setelah berhasil
        self.assertEqual(response.status_code, 302)

        # Status berubah jadi batal
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "batal")

        # Alasan tersimpan
        self.assertEqual(
            self.transaksi.alasan_batal, "Pelanggan membatalkan pesanan mendadak"
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
            no_transaksi="SW20260506KRYW2",
            pelanggan_nama="Pelanggan Karyawan 2",
            pelanggan_hp="08100000004",
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date(2026, 5, 8),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="menunggu",
            dibuat_oleh=self.karyawan,  # milik karyawan
        )
        DetailTransaksi.objects.create(
            transaksi=transaksi_karyawan,
            barang=self.barang,
            jumlah=1,
            jumlah_hari=1,
            harga_satuan=Decimal("50000"),
            subtotal=Decimal("50000"),
        )

        self.client.login(username="karyawan_batal", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_batal", args=[transaksi_karyawan.pk]),
            {"alasan_batal": "Barang tidak tersedia sesuai permintaan"},
        )
        self.assertEqual(response.status_code, 302)

        transaksi_karyawan.refresh_from_db()
        self.assertEqual(transaksi_karyawan.status, "batal")
        self.assertEqual(transaksi_karyawan.dibatalkan_oleh, self.karyawan)

    def test_transaksi_selesai_tidak_bisa_dibatalkan(self):
        """Test transaksi yang sudah selesai tidak bisa dibatalkan"""
        self.transaksi.status = "selesai"
        self.transaksi.save()

        self.client.login(username="admin_batal", password="admin123")
        response = self.client.get(reverse("transaksi_batal", args=[self.transaksi.pk]))
        # Harus 404 karena filter status='aktif' di view
        self.assertEqual(response.status_code, 404)

    def test_transaksi_batal_tidak_bisa_dibatalkan_lagi(self):
        """Test transaksi yang sudah batal tidak bisa dibatalkan lagi"""
        self.transaksi.status = "batal"
        self.transaksi.save()

        self.client.login(username="admin_batal", password="admin123")
        response = self.client.get(reverse("transaksi_batal", args=[self.transaksi.pk]))
        # Harus 404
        self.assertEqual(response.status_code, 404)

    def test_dibatalkan_at_tersimpan(self):
        """Test waktu pembatalan tersimpan"""
        self.client.login(username="admin_batal", password="admin123")
        self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]),
            {"alasan_batal": "Test waktu pembatalan"},
        )
        self.transaksi.refresh_from_db()
        self.assertIsNotNone(self.transaksi.dibatalkan_at)


class StatusTransaksiViewTest(TestCase):
    """Test alur perubahan status transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_status", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_status", password="admin123")

        self.barang = Barang.objects.create(
            kode="ST001",
            nama="Barang Status Test",
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("20000"),
            kondisi="baik",
        )

        # Transaksi awal status menunggu
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260507ST1",
            pelanggan_nama="Test Status",
            pelanggan_hp="08100000002",
            tanggal_sewa=datetime.date(2026, 5, 7),
            tanggal_kembali=datetime.date(2026, 5, 9),
            uang_muka=Decimal("0"),
            total_harga=Decimal("80000"),
            sisa_bayar=Decimal("80000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )
        self.detail = DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal("20000"),
            subtotal=Decimal("80000"),
        )
        # Stok sudah dikunci saat menunggu
        self.barang.stok_tersedia -= 2
        self.barang.save()

    def test_status_awal_adalah_menunggu(self):
        """Test transaksi baru selalu status menunggu"""
        self.assertEqual(self.transaksi.status, "menunggu")

    def test_menunggu_ke_siap_diambil(self):
        """Test ubah status dari menunggu ke siap diambil"""
        response = self.client.post(
            reverse("transaksi_siap_diambil", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "siap_diambil")

    def test_siap_diambil_ke_disewa(self):
        """Test ubah status dari siap diambil ke disewa"""
        self.transaksi.status = "siap_diambil"
        self.transaksi.save()

        response = self.client.post(
            reverse("transaksi_disewa", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "disewa")

    def test_disewa_ke_selesai(self):
        """Test ubah status dari disewa ke selesai"""
        self.transaksi.status = "disewa"
        self.transaksi.save()

        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi.pk]),
            {f"kondisi_kembali_{self.detail.pk}": "Baik"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "selesai")

    def test_tidak_bisa_skip_menunggu_ke_disewa(self):
        """Test tidak bisa langsung dari menunggu ke disewa"""
        # Status masih menunggu, coba akses transaksi_disewa
        response = self.client.post(
            reverse("transaksi_disewa", args=[self.transaksi.pk])
        )
        # Harus 404 karena filter status='siap_diambil'
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "menunggu")

    def test_tidak_bisa_kembali_dari_menunggu(self):
        """Test tidak bisa proses kembali dari status menunggu"""
        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi.pk]),
            {f"kondisi_kembali_{self.detail.pk}": "Baik"},
        )
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "menunggu")

    def test_tidak_bisa_kembali_dari_siap_diambil(self):
        """Test tidak bisa proses kembali dari status siap diambil"""
        self.transaksi.status = "siap_diambil"
        self.transaksi.save()

        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi.pk]),
            {f"kondisi_kembali_{self.detail.pk}": "Baik"},
        )
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "siap_diambil")

    def test_batal_dari_menunggu(self):
        """Test bisa batalkan dari status menunggu"""
        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]),
            {"alasan_batal": "Dibatalkan dari menunggu"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "batal")

        # Stok kembali normal
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_batal_dari_siap_diambil(self):
        """Test bisa batalkan dari status siap diambil"""
        self.transaksi.status = "siap_diambil"
        self.transaksi.save()

        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]),
            {"alasan_batal": "Dibatalkan dari siap diambil"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "batal")

        # Stok kembali normal
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_tidak_bisa_batal_dari_disewa(self):
        """Test tidak bisa batalkan dari status disewa"""
        self.transaksi.status = "disewa"
        self.transaksi.save()

        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]),
            {"alasan_batal": "Coba batalkan dari disewa"},
        )
        # Harus 404 karena filter status__in=['menunggu', 'siap_diambil']
        self.assertEqual(response.status_code, 404)
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.status, "disewa")

    def test_tidak_bisa_batal_dari_selesai(self):
        """Test tidak bisa batalkan dari status selesai"""
        self.transaksi.status = "selesai"
        self.transaksi.save()

        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi.pk]),
            {"alasan_batal": "Coba batalkan dari selesai"},
        )
        self.assertEqual(response.status_code, 404)

    def test_stok_dikunci_saat_menunggu(self):
        """Test stok sudah berkurang saat status menunggu"""
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 8)
        self.assertEqual(self.barang.stok_disewa, 2)

    def test_stok_kembali_saat_selesai(self):
        """Test stok kembali normal saat selesai"""
        self.transaksi.status = "disewa"
        self.transaksi.save()

        self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi.pk]),
            {f"kondisi_kembali_{self.detail.pk}": "Baik"},
        )
        self.barang.refresh_from_db()
        self.assertEqual(self.barang.stok_tersedia, 10)

    def test_halaman_konfirmasi_siap_diambil_tampil(self):
        """Test halaman konfirmasi siap diambil bisa diakses"""
        response = self.client.get(
            reverse("transaksi_siap_diambil", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_konfirmasi.html")

    def test_halaman_konfirmasi_disewa_tampil(self):
        """Test halaman konfirmasi disewa bisa diakses"""
        self.transaksi.status = "siap_diambil"
        self.transaksi.save()

        response = self.client.get(
            reverse("transaksi_disewa", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_konfirmasi.html")


class AksesKaryawanTest(TestCase):
    """Test akses karyawan opsi 3"""

    def setUp(self):
        self.client = Client()

        # Buat admin
        self.admin = User.objects.create_user(
            username="admin_akses", password="admin123"
        )
        UserProfile.objects.create(user=self.admin, role="admin")

        # Buat karyawan A
        self.karyawan_a = User.objects.create_user(
            username="karyawan_a", password="karyawan123"
        )
        UserProfile.objects.create(user=self.karyawan_a, role="karyawan")

        # Buat karyawan B
        self.karyawan_b = User.objects.create_user(
            username="karyawan_b", password="karyawan123"
        )
        UserProfile.objects.create(user=self.karyawan_b, role="karyawan")

        # Buat barang
        self.barang = Barang.objects.create(
            kode="AK001",
            nama="Barang Akses Test",
            stok_total=20,
            stok_tersedia=20,
            harga_sewa=Decimal("10000"),
            kondisi="baik",
        )

        # Transaksi milik karyawan A - status menunggu
        self.transaksi_a_menunggu = Transaksi.objects.create(
            no_transaksi="SW20260508AK1",
            pelanggan_nama="Pelanggan A",
            pelanggan_hp="08100000010",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            total_harga=Decimal("40000"),
            sisa_bayar=Decimal("40000"),
            status="menunggu",
            dibuat_oleh=self.karyawan_a,
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi_a_menunggu,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal("10000"),
            subtotal=Decimal("40000"),
        )
        self.barang.stok_tersedia -= 2
        self.barang.save()

        # Transaksi milik karyawan A - status siap diambil
        self.transaksi_a_siap = Transaksi.objects.create(
            no_transaksi="SW20260508AK2",
            pelanggan_nama="Pelanggan A2",
            pelanggan_hp="08100000011",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            total_harga=Decimal("20000"),
            sisa_bayar=Decimal("20000"),
            status="siap_diambil",
            dibuat_oleh=self.karyawan_a,
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi_a_siap,
            barang=self.barang,
            jumlah=1,
            jumlah_hari=2,
            harga_satuan=Decimal("10000"),
            subtotal=Decimal("20000"),
        )
        self.barang.stok_tersedia -= 1
        self.barang.save()

        # Transaksi milik karyawan A - status disewa
        self.transaksi_a_disewa = Transaksi.objects.create(
            no_transaksi="SW20260508AK3",
            pelanggan_nama="Pelanggan A3",
            pelanggan_hp="08100000012",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            total_harga=Decimal("20000"),
            sisa_bayar=Decimal("20000"),
            status="disewa",
            dibuat_oleh=self.karyawan_a,
        )
        self.detail_disewa = DetailTransaksi.objects.create(
            transaksi=self.transaksi_a_disewa,
            barang=self.barang,
            jumlah=1,
            jumlah_hari=2,
            harga_satuan=Decimal("10000"),
            subtotal=Decimal("20000"),
        )
        self.barang.stok_tersedia -= 1
        self.barang.save()

    # ===========================
    # TEST KARYAWAN B (bukan pembuat)
    # ===========================

    def test_karyawan_lain_tidak_bisa_siap_diambil(self):
        """Test karyawan B tidak bisa proses siap diambil transaksi karyawan A"""
        self.client.login(username="karyawan_b", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_siap_diambil", args=[self.transaksi_a_menunggu.pk])
        )
        # Redirect ke detail dengan pesan error
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        # Status tidak berubah
        self.assertEqual(self.transaksi_a_menunggu.status, "menunggu")

    def test_karyawan_lain_tidak_bisa_disewa(self):
        """Test karyawan B tidak bisa proses barang keluar transaksi karyawan A"""
        self.client.login(username="karyawan_b", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_disewa", args=[self.transaksi_a_siap.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_siap.refresh_from_db()
        self.assertEqual(self.transaksi_a_siap.status, "siap_diambil")

    def test_karyawan_lain_tidak_bisa_kembali(self):
        """Test karyawan B tidak bisa proses pengembalian transaksi karyawan A"""
        self.client.login(username="karyawan_b", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi_a_disewa.pk]),
            {f"kondisi_kembali_{self.detail_disewa.pk}": "Baik"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_disewa.refresh_from_db()
        # Status tidak berubah
        self.assertEqual(self.transaksi_a_disewa.status, "disewa")

    def test_karyawan_lain_tidak_bisa_batal(self):
        """Test karyawan B tidak bisa batalkan transaksi karyawan A"""
        self.client.login(username="karyawan_b", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi_a_menunggu.pk]),
            {"alasan_batal": "Coba batalkan transaksi orang lain"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, "menunggu")

    def test_karyawan_lain_bisa_lihat_detail(self):
        """Test karyawan B bisa lihat detail transaksi karyawan A"""
        self.client.login(username="karyawan_b", password="karyawan123")
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_karyawan_lain_tidak_ada_tombol_aksi(self):
        """Test karyawan B tidak lihat tombol aksi di detail transaksi karyawan A"""
        self.client.login(username="karyawan_b", password="karyawan123")
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)
        # Tombol aksi tidak tampil
        self.assertNotContains(response, "Siapkan Barang")
        self.assertNotContains(response, "Barang Keluar")
        self.assertNotContains(response, "Proses Pengembalian")

    def test_karyawan_sendiri_ada_tombol_aksi(self):
        """Test karyawan A lihat tombol aksi di transaksi miliknya"""
        self.client.login(username="karyawan_a", password="karyawan123")
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)
        # Tombol aksi tampil
        self.assertContains(response, "Siapkan Barang")

    # ===========================
    # TEST KARYAWAN A (pembuat)
    # ===========================

    def test_karyawan_sendiri_bisa_siap_diambil(self):
        """Test karyawan A bisa proses siap diambil transaksi miliknya"""
        self.client.login(username="karyawan_a", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_siap_diambil", args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, "siap_diambil")

    def test_karyawan_sendiri_bisa_disewa(self):
        """Test karyawan A bisa proses barang keluar transaksi miliknya"""
        self.client.login(username="karyawan_a", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_disewa", args=[self.transaksi_a_siap.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_siap.refresh_from_db()
        self.assertEqual(self.transaksi_a_siap.status, "disewa")

    def test_karyawan_sendiri_bisa_kembali(self):
        """Test karyawan A bisa proses pengembalian transaksi miliknya"""
        self.client.login(username="karyawan_a", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi_a_disewa.pk]),
            {f"kondisi_kembali_{self.detail_disewa.pk}": "Baik"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_disewa.refresh_from_db()
        self.assertEqual(self.transaksi_a_disewa.status, "selesai")

    def test_karyawan_sendiri_bisa_batal(self):
        """Test karyawan A bisa batalkan transaksi miliknya"""
        self.client.login(username="karyawan_a", password="karyawan123")
        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi_a_menunggu.pk]),
            {"alasan_batal": "Dibatalkan oleh karyawan sendiri"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, "batal")

    # ===========================
    # TEST ADMIN (bisa semua)
    # ===========================

    def test_admin_bisa_siap_diambil_transaksi_karyawan(self):
        """Test admin bisa proses siap diambil transaksi milik karyawan"""
        self.client.login(username="admin_akses", password="admin123")
        response = self.client.post(
            reverse("transaksi_siap_diambil", args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, "siap_diambil")

    def test_admin_bisa_disewa_transaksi_karyawan(self):
        """Test admin bisa proses barang keluar transaksi milik karyawan"""
        self.client.login(username="admin_akses", password="admin123")
        response = self.client.post(
            reverse("transaksi_disewa", args=[self.transaksi_a_siap.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_siap.refresh_from_db()
        self.assertEqual(self.transaksi_a_siap.status, "disewa")

    def test_admin_bisa_kembali_transaksi_karyawan(self):
        """Test admin bisa proses pengembalian transaksi milik karyawan"""
        self.client.login(username="admin_akses", password="admin123")
        response = self.client.post(
            reverse("transaksi_kembali", args=[self.transaksi_a_disewa.pk]),
            {f"kondisi_kembali_{self.detail_disewa.pk}": "Baik"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_disewa.refresh_from_db()
        self.assertEqual(self.transaksi_a_disewa.status, "selesai")

    def test_admin_bisa_batal_transaksi_karyawan(self):
        """Test admin bisa batalkan transaksi milik karyawan"""
        self.client.login(username="admin_akses", password="admin123")
        response = self.client.post(
            reverse("transaksi_batal", args=[self.transaksi_a_menunggu.pk]),
            {"alasan_batal": "Dibatalkan oleh admin"},
        )
        self.assertEqual(response.status_code, 302)
        self.transaksi_a_menunggu.refresh_from_db()
        self.assertEqual(self.transaksi_a_menunggu.status, "batal")

    def test_admin_ada_tombol_aksi_di_semua_transaksi(self):
        """Test admin lihat tombol aksi di semua transaksi"""
        self.client.login(username="admin_akses", password="admin123")
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi_a_menunggu.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Siapkan Barang")


class PrintPersiapanViewTest(TestCase):
    """Test fitur print persiapan barang untuk gudang"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_print", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_print", password="admin123")

        # Buat gudang
        from apps.inventory.models import Gudang

        self.gudang_andir = Gudang.objects.create(
            nama="Gudang Andir", alamat="Jl. Andir No. 1", aktif=True
        )
        self.gudang_kubang = Gudang.objects.create(
            nama="Gudang Kubang", alamat="Jl. Kubang No. 2", aktif=True
        )

        # Buat kategori dan barang
        self.kategori = Kategori.objects.create(nama="Kursi")
        self.barang_andir = Barang.objects.create(
            kode="PR001",
            nama="Kursi Andir",
            kategori=self.kategori,
            gudang=self.gudang_andir,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("10000"),
            kondisi="baik",
        )
        self.barang_kubang = Barang.objects.create(
            kode="PR002",
            nama="Kursi Kubang",
            kategori=self.kategori,
            gudang=self.gudang_kubang,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("15000"),
            kondisi="baik",
        )
        self.barang_tanpa_gudang = Barang.objects.create(
            kode="PR003",
            nama="Kursi Tanpa Gudang",
            kategori=self.kategori,
            gudang=None,
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal("12000"),
            kondisi="baik",
        )

        # Buat pelanggan
        self.pelanggan = Pelanggan.objects.create(
            nama="Siti Aminah", hp="08199998888", alamat="Jl. Bandung No. 10"
        )

        # Buat transaksi lengkap
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260508PR1",
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            pelanggan_alamat=self.pelanggan.alamat,
            acara="Pernikahan Siti",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("100000"),
            total_harga=Decimal("350000"),
            sisa_bayar=Decimal("250000"),
            catatan="Mohon disiapkan dengan hati-hati",
            status="menunggu",
            dibuat_oleh=self.user,
        )

        # Detail barang dari 2 gudang berbeda
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang_andir,
            jumlah=5,
            jumlah_hari=2,
            harga_satuan=Decimal("10000"),
            subtotal=Decimal("100000"),
            kondisi_keluar="Baik",
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang_kubang,
            jumlah=3,
            jumlah_hari=2,
            harga_satuan=Decimal("15000"),
            subtotal=Decimal("90000"),
            kondisi_keluar="Baik",
        )

    def test_halaman_print_bisa_diakses(self):
        """Test halaman print persiapan bisa diakses"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_print_persiapan.html")

    def test_print_tampilkan_info_pelanggan(self):
        """Test halaman print menampilkan info pelanggan"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Siti Aminah")
        self.assertContains(response, "08199998888")
        self.assertContains(response, "Jl. Bandung No. 10")
        self.assertContains(response, "Pernikahan Siti")

    def test_print_tampilkan_info_transaksi(self):
        """Test halaman print menampilkan info transaksi"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "SW20260508PR1")
        self.assertContains(response, "08 Mei 2026")

    def test_print_tampilkan_nama_gudang(self):
        """Test halaman print menampilkan nama gudang"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Gudang Andir")
        self.assertContains(response, "Gudang Kubang")

    def test_print_tampilkan_alamat_gudang(self):
        """Test halaman print menampilkan alamat gudang"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Jl. Andir No. 1")
        self.assertContains(response, "Jl. Kubang No. 2")

    def test_print_tampilkan_nama_barang(self):
        """Test halaman print menampilkan nama barang"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Kursi Andir")
        self.assertContains(response, "Kursi Kubang")

    def test_print_tampilkan_jumlah_barang(self):
        """Test halaman print menampilkan jumlah barang"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "5")
        self.assertContains(response, "3")

    def test_print_tidak_tampilkan_harga(self):
        """Test halaman print tidak menampilkan harga"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        # Harga tidak boleh tampil
        self.assertNotContains(response, "Rp 10000")
        self.assertNotContains(response, "Rp 15000")
        self.assertNotContains(response, "Rp 350000")
        self.assertNotContains(response, "Subtotal")
        self.assertNotContains(response, "Total")

    def test_print_tampilkan_catatan(self):
        """Test halaman print menampilkan catatan transaksi"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Mohon disiapkan dengan hati-hati")

    def test_print_tampilkan_kolom_checklist(self):
        """Test halaman print ada kolom checklist untuk gudang"""
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertContains(response, "check-box")

    def test_print_bisa_diakses_karyawan(self):
        """Test karyawan juga bisa akses halaman print"""
        karyawan = User.objects.create_user(
            username="karyawan_print", password="karyawan123"
        )
        UserProfile.objects.create(user=karyawan, role="karyawan")
        self.client.login(username="karyawan_print", password="karyawan123")
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_print_redirect_kalau_belum_login(self):
        """Test redirect ke login kalau belum login"""
        self.client.logout()
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_print_transaksi_tidak_ada_404(self):
        """Test transaksi tidak ada return 404"""
        response = self.client.get(reverse("transaksi_print_persiapan", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_print_barang_tanpa_gudang(self):
        """Test print tetap bisa tampil meski ada barang tanpa gudang"""
        # Tambah barang tanpa gudang ke transaksi
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang_tanpa_gudang,
            jumlah=2,
            jumlah_hari=2,
            harga_satuan=Decimal("12000"),
            subtotal=Decimal("48000"),
            kondisi_keluar="Baik",
        )
        response = self.client.get(
            reverse("transaksi_print_persiapan", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kursi Tanpa Gudang")


class AutocompletePelangganTest(TestCase):
    """Test API autocomplete pencarian pelanggan"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_autocomplete", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_autocomplete", password="admin123")

        # Buat beberapa pelanggan
        self.pelanggan1 = Pelanggan.objects.create(
            nama="Siti Rahayu", hp="08111111111", alamat="Bandung"
        )
        self.pelanggan2 = Pelanggan.objects.create(
            nama="Siti Aminah", hp="08222222222", alamat="Cimahi"
        )
        self.pelanggan3 = Pelanggan.objects.create(
            nama="Budi Santoso", hp="08333333333", alamat="Garut"
        )

    def test_api_return_hasil_pencarian(self):
        """Test API return data pelanggan yang cocok"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "Siti"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["results"]), 2)

    def test_api_cari_by_nama(self):
        """Test API bisa cari berdasarkan nama"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "Budi"})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["nama"], "Budi Santoso")

    def test_api_cari_by_hp(self):
        """Test API bisa cari berdasarkan nomor HP"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "08111"})
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["hp"], "08111111111")

    def test_api_query_kurang_2_karakter(self):
        """Test API return kosong kalau query kurang dari 2 karakter"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "S"})
        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_api_query_kosong(self):
        """Test API return kosong kalau query kosong"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": ""})
        data = response.json()
        self.assertEqual(len(data["results"]), 0)

    def test_api_return_field_yang_benar(self):
        """Test API return field id, nama, hp, alamat"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "Budi"})
        data = response.json()
        result = data["results"][0]
        self.assertIn("id", result)
        self.assertIn("nama", result)
        self.assertIn("hp", result)
        self.assertIn("alamat", result)

    def test_api_redirect_kalau_belum_login(self):
        """Test API redirect ke login kalau belum login"""
        self.client.logout()
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "Siti"})
        self.assertEqual(response.status_code, 302)

    def test_api_tidak_ditemukan(self):
        """Test API return kosong kalau tidak ada yang cocok"""
        response = self.client.get(reverse("pelanggan_search_api"), {"q": "XYZABC"})
        data = response.json()
        self.assertEqual(len(data["results"]), 0)


class PrintLaporanTest(TestCase):
    """Test halaman print laporan keuangan dan barang"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_laporan_print", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_laporan_print", password="admin123")

        # Buat data transaksi selesai
        self.pelanggan = Pelanggan.objects.create(nama="Test Laporan", hp="08100000099")
        self.barang = Barang.objects.create(
            kode="LP001",
            nama="Barang Laporan",
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("50000"),
            kondisi="baik",
        )
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260508LP1",
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            tanggal_sewa=datetime.date(2026, 5, 1),
            tanggal_kembali=datetime.date(2026, 5, 3),
            tanggal_kembali_aktual=datetime.date(2026, 5, 3),
            uang_muka=Decimal("100000"),
            total_harga=Decimal("300000"),
            sisa_bayar=Decimal("200000"),
            status="selesai",
            dibuat_oleh=self.user,
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=2,
            jumlah_hari=3,
            harga_satuan=Decimal("50000"),
            subtotal=Decimal("300000"),
        )

    def test_print_laporan_keuangan_bisa_diakses(self):
        """Test halaman print laporan keuangan bisa diakses"""
        response = self.client.get(
            reverse("laporan_keuangan"), {"bulan": 5, "tahun": 2026, "pdf": 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/keuangan_print.html")

    def test_print_laporan_keuangan_tampilkan_data(self):
        """Test print laporan keuangan tampilkan data transaksi"""
        response = self.client.get(
            reverse("laporan_keuangan"), {"bulan": 5, "tahun": 2026, "pdf": 1}
        )
        self.assertContains(response, "SW20260508LP1")
        self.assertContains(response, "Test Laporan")

    def test_print_laporan_keuangan_tampilkan_total(self):
        """Test print laporan keuangan tampilkan total omzet"""
        response = self.client.get(
            reverse("laporan_keuangan"), {"bulan": 5, "tahun": 2026, "pdf": 1}
        )
        self.assertContains(response, "300.000")

    def test_print_laporan_keuangan_filter_bulan_kosong(self):
        """Test print laporan bulan lain tidak tampilkan data"""
        response = self.client.get(
            reverse("laporan_keuangan"), {"bulan": 1, "tahun": 2026, "pdf": 1}
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "SW20260508LP1")

    def test_print_laporan_barang_bisa_diakses(self):
        """Test halaman print laporan barang bisa diakses"""
        response = self.client.get(reverse("laporan_barang"), {"pdf": 1})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/barang_print.html")

    def test_print_laporan_barang_tampilkan_data(self):
        """Test print laporan barang tampilkan data barang"""
        response = self.client.get(reverse("laporan_barang"), {"pdf": 1})
        self.assertContains(response, "Barang Laporan")

    def test_print_redirect_kalau_belum_login(self):
        """Test redirect ke login kalau belum login"""
        self.client.logout()
        response = self.client.get(reverse("laporan_keuangan"), {"pdf": 1})
        self.assertEqual(response.status_code, 302)


class JadwalViewTest(TestCase):
    """Test jadwal menampilkan semua status transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_jadwal", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_jadwal", password="admin123")

        # Transaksi menunggu
        self.trx_menunggu = Transaksi.objects.create(
            no_transaksi="SW20260508JD1",
            pelanggan_nama="Pelanggan Menunggu",
            pelanggan_hp="08100000020",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )

        # Transaksi siap diambil
        self.trx_siap = Transaksi.objects.create(
            no_transaksi="SW20260508JD2",
            pelanggan_nama="Pelanggan Siap",
            pelanggan_hp="08100000021",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="siap_diambil",
            dibuat_oleh=self.user,
        )

        # Transaksi disewa - kembali hari ini
        self.trx_disewa_hari_ini = Transaksi.objects.create(
            no_transaksi="SW20260508JD3",
            pelanggan_nama="Pelanggan Disewa",
            pelanggan_hp="08100000022",
            tanggal_sewa=datetime.date(2026, 5, 6),
            tanggal_kembali=datetime.date.today(),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="disewa",
            dibuat_oleh=self.user,
        )

        # Transaksi disewa - terlambat
        self.trx_terlambat = Transaksi.objects.create(
            no_transaksi="SW20260508JD4",
            pelanggan_nama="Pelanggan Terlambat",
            pelanggan_hp="08100000023",
            tanggal_sewa=datetime.date(2026, 5, 1),
            tanggal_kembali=datetime.date(2026, 5, 3),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="disewa",
            dibuat_oleh=self.user,
        )

        # Transaksi disewa - akan datang
        self.trx_akan_datang = Transaksi.objects.create(
            no_transaksi="SW20260508JD5",
            pelanggan_nama="Pelanggan Akan Datang",
            pelanggan_hp="08100000024",
            tanggal_sewa=datetime.date(2026, 5, 8),
            tanggal_kembali=datetime.date(2026, 5, 20),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="disewa",
            dibuat_oleh=self.user,
        )

    def test_jadwal_bisa_diakses(self):
        """Test halaman jadwal bisa diakses"""
        response = self.client.get(reverse("jadwal"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/jadwal.html")

    def test_jadwal_tampilkan_menunggu(self):
        """Test jadwal tampilkan transaksi menunggu"""
        response = self.client.get(reverse("jadwal"))
        self.assertContains(response, "SW20260508JD1")
        self.assertContains(response, "Pelanggan Menunggu")

    def test_jadwal_tampilkan_siap_diambil(self):
        """Test jadwal tampilkan transaksi siap diambil"""
        response = self.client.get(reverse("jadwal"))
        self.assertContains(response, "SW20260508JD2")
        self.assertContains(response, "Pelanggan Siap")

    def test_jadwal_tampilkan_kembali_hari_ini(self):
        """Test jadwal tampilkan transaksi kembali hari ini"""
        response = self.client.get(reverse("jadwal"))
        self.assertContains(response, "SW20260508JD3")

    def test_jadwal_tampilkan_terlambat(self):
        """Test jadwal tampilkan transaksi terlambat"""
        response = self.client.get(reverse("jadwal"))
        self.assertContains(response, "SW20260508JD4")
        self.assertContains(response, "Pelanggan Terlambat")

    def test_jadwal_tampilkan_akan_datang(self):
        """Test jadwal tampilkan transaksi akan datang"""
        response = self.client.get(reverse("jadwal"))
        self.assertContains(response, "SW20260508JD5")
        self.assertContains(response, "Pelanggan Akan Datang")

    def test_jadwal_redirect_kalau_belum_login(self):
        """Test jadwal redirect ke login kalau belum login"""
        self.client.logout()
        response = self.client.get(reverse("jadwal"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_jadwal_tidak_tampilkan_selesai(self):
        """Test jadwal tidak tampilkan transaksi selesai"""
        Transaksi.objects.create(
            no_transaksi="SW20260508JD6",
            pelanggan_nama="Pelanggan Selesai",
            pelanggan_hp="08100000025",
            tanggal_sewa=datetime.date(2026, 5, 1),
            tanggal_kembali=datetime.date(2026, 5, 3),
            tanggal_kembali_aktual=datetime.date(2026, 5, 3),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="selesai",
            dibuat_oleh=self.user,
        )
        response = self.client.get(reverse("jadwal"))
        self.assertNotContains(response, "SW20260508JD6")

    def test_jadwal_tidak_tampilkan_batal(self):
        """Test jadwal tidak tampilkan transaksi batal"""
        Transaksi.objects.create(
            no_transaksi="SW20260508JD7",
            pelanggan_nama="Pelanggan Batal",
            pelanggan_hp="08100000026",
            tanggal_sewa=datetime.date(2026, 5, 1),
            tanggal_kembali=datetime.date(2026, 5, 3),
            uang_muka=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="batal",
            alasan_batal="Test",
            dibuat_oleh=self.user,
        )
        response = self.client.get(reverse("jadwal"))
        self.assertNotContains(response, "SW20260508JD7")


class SearchBarangFormTest(TestCase):
    """Test fitur search barang di form transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_search_barang", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_search_barang", password="admin123")

        # Buat gudang
        from apps.inventory.models import Gudang

        self.gudang_andir = Gudang.objects.create(
            nama="Gudang Andir", alamat="Jl. Andir No. 1", aktif=True
        )
        self.gudang_kubang = Gudang.objects.create(
            nama="Gudang Kubang", alamat="Jl. Kubang No. 2", aktif=True
        )

        # Buat kategori
        self.kategori = Kategori.objects.create(nama="Kursi")

        # Buat barang dengan stok tersedia
        self.barang_andir = Barang.objects.create(
            kode="SB001",
            nama="Kursi Tiffany Gold",
            kategori=self.kategori,
            gudang=self.gudang_andir,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("15000"),
            kondisi="baik",
        )
        self.barang_kubang = Barang.objects.create(
            kode="SB002",
            nama="Meja Bundar Putih",
            kategori=self.kategori,
            gudang=self.gudang_kubang,
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal("25000"),
            kondisi="baik",
        )

        # Barang habis stok - tidak boleh muncul di form
        self.barang_habis = Barang.objects.create(
            kode="SB003",
            nama="Tenda Habis",
            kategori=self.kategori,
            gudang=self.gudang_andir,
            stok_total=5,
            stok_tersedia=0,
            harga_sewa=Decimal("50000"),
            kondisi="baik",
        )

        # Barang rusak - tidak boleh muncul di form
        self.barang_rusak = Barang.objects.create(
            kode="SB004",
            nama="Kursi Rusak",
            kategori=self.kategori,
            gudang=self.gudang_andir,
            stok_total=5,
            stok_tersedia=5,
            harga_sewa=Decimal("10000"),
            kondisi="rusak_berat",
        )

    def test_form_transaksi_tampil_barang_tersedia(self):
        """Test form transaksi tampilkan barang yang tersedia"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertEqual(response.status_code, 200)
        # Barang tersedia tampil
        self.assertContains(response, "Kursi Tiffany Gold")
        self.assertContains(response, "Meja Bundar Putih")

    def test_form_transaksi_tidak_tampil_barang_habis(self):
        """Test form transaksi tidak tampilkan barang habis stok"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertNotContains(response, "Tenda Habis")

    def test_form_transaksi_tidak_tampil_barang_rusak(self):
        """Test form transaksi tidak tampilkan barang rusak"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertNotContains(response, "Kursi Rusak")

    def test_form_transaksi_tampil_info_gudang(self):
        """Test form transaksi tampilkan info gudang barang"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertContains(response, "Gudang Andir")
        self.assertContains(response, "Gudang Kubang")

    def test_form_transaksi_tampil_alamat_gudang(self):
        """Test form transaksi tampilkan alamat gudang"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertContains(response, "Jl. Andir No. 1")
        self.assertContains(response, "Jl. Kubang No. 2")

    def test_form_transaksi_tampil_harga_barang(self):
        """Test form transaksi tampilkan harga barang"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertContains(response, "15000")
        self.assertContains(response, "25000")

    def test_form_transaksi_tampil_stok_barang(self):
        """Test form transaksi tampilkan stok barang"""
        response = self.client.get(reverse("transaksi_create"))
        content = response.content.decode("utf-8")
        # Cek stok nilai ada di JavaScript data
        self.assertIn("stok: 10", content)
        self.assertIn("stok: 5", content)

    def test_form_transaksi_tampil_kode_barang(self):
        """Test form transaksi tampilkan kode barang"""
        response = self.client.get(reverse("transaksi_create"))
        self.assertContains(response, "SB001")
        self.assertContains(response, "SB002")

    def test_transaksi_create_dengan_barang_dari_search(self):
        """Test buat transaksi berhasil dengan barang yang dipilih"""
        pelanggan = Pelanggan.objects.create(nama="Test Search", hp="08100000030")
        response = self.client.post(
            reverse("transaksi_create"),
            {
                "pelanggan_id": pelanggan.pk,
                "tanggal_sewa": "2026-05-08",
                "tanggal_kembali": "2026-05-10",
                "acara": "Pernikahan Test",
                "uang_muka": "50000",
                "diskon": "0",  # tambah ini
                "catatan": "",
                "barang_id": [self.barang_andir.pk],
                "jumlah": ["3"],
                f"kondisi_keluar_{self.barang_andir.pk}": "Baik",
            },
        )
        self.assertEqual(response.status_code, 302)
        transaksi = Transaksi.objects.filter(pelanggan_nama="Test Search").first()
        self.assertIsNotNone(transaksi)
        self.barang_andir.refresh_from_db()
        self.assertEqual(self.barang_andir.stok_tersedia, 7)
        detail = transaksi.detail.first()
        self.assertEqual(detail.subtotal, Decimal("90000"))
        self.assertEqual(detail.jumlah_hari, 2)

    def test_transaksi_create_stok_tidak_cukup(self):
        """Test buat transaksi gagal kalau stok tidak cukup"""
        pelanggan = Pelanggan.objects.create(nama="Test Stok Kurang", hp="08100000031")
        response = self.client.post(
            reverse("transaksi_create"),
            {
                "pelanggan_id": pelanggan.pk,
                "tanggal_sewa": "2026-05-08",
                "tanggal_kembali": "2026-05-10",
                "uang_muka": "0",
                "barang_id": [self.barang_andir.pk],
                "jumlah": ["999"],  # melebihi stok
                f"kondisi_keluar_{self.barang_andir.pk}": "Baik",
            },
        )
        # Tidak redirect, tetap di halaman form dengan pesan error
        self.assertEqual(response.status_code, 200)

        # Stok tidak berubah
        self.barang_andir.refresh_from_db()
        self.assertEqual(self.barang_andir.stok_tersedia, 10)

    def test_transaksi_create_multi_barang(self):
        """Test buat transaksi dengan beberapa barang dari gudang berbeda"""
        pelanggan = Pelanggan.objects.create(nama="Test Multi Barang", hp="08100000032")
        response = self.client.post(
            reverse("transaksi_create"),
            {
                "pelanggan_id": pelanggan.pk,
                "tanggal_sewa": "2026-05-08",
                "tanggal_kembali": "2026-05-09",
                "uang_muka": "0",
                "diskon": "0",  # tambah ini
                "barang_id": [self.barang_andir.pk, self.barang_kubang.pk],
                "jumlah": ["2", "1"],
                f"kondisi_keluar_{self.barang_andir.pk}": "Baik",
                f"kondisi_keluar_{self.barang_kubang.pk}": "Baik",
            },
        )
        self.assertEqual(response.status_code, 302)
        transaksi = Transaksi.objects.filter(pelanggan_nama="Test Multi Barang").first()
        self.assertIsNotNone(transaksi)
        self.assertEqual(transaksi.detail.count(), 2)
        self.barang_andir.refresh_from_db()
        self.barang_kubang.refresh_from_db()
        self.assertEqual(self.barang_andir.stok_tersedia, 8)
        self.assertEqual(self.barang_kubang.stok_tersedia, 4)
        self.assertEqual(transaksi.total_harga, Decimal("55000"))


class PaginationTest(TestCase):
    """Test pagination di daftar transaksi, barang, dan pelanggan"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_pagination", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_pagination", password="admin123")

        self.kategori = Kategori.objects.create(nama="Test")

        # Buat 25 transaksi
        for i in range(25):
            Transaksi.objects.create(
                no_transaksi=f"SW2026050900{i:02d}",
                pelanggan_nama=f"Pelanggan {i}",
                pelanggan_hp=f"0810000{i:04d}",
                tanggal_sewa=datetime.date(2026, 5, 9),
                tanggal_kembali=datetime.date(2026, 5, 11),
                uang_muka=Decimal("0"),
                total_harga=Decimal("100000"),
                sisa_bayar=Decimal("100000"),
                status="menunggu" if i % 2 == 0 else "disewa",
                dibuat_oleh=self.user,
            )

        # Buat 25 barang
        for i in range(25):
            Barang.objects.create(
                kode=f"BRG{i:03d}",
                nama=f"Barang {i}",
                kategori=self.kategori,
                stok_total=10,
                stok_tersedia=10,
                harga_sewa=Decimal("10000"),
                kondisi="baik",
            )

        # Buat 25 pelanggan
        for i in range(25):
            Pelanggan.objects.create(
                nama=f"Pelanggan Paginasi {i}",
                hp=f"0820000{i:04d}",
            )

    # ===========================
    # TEST TRANSAKSI
    # ===========================

    def test_transaksi_list_halaman_1(self):
        """Test daftar transaksi halaman 1 tampil 20 data"""
        response = self.client.get(reverse("transaksi_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["transaksi_list"]), 10)

    def test_transaksi_list_halaman_2(self):
        """Test daftar transaksi halaman 3 tampil sisa data"""
        response = self.client.get(reverse("transaksi_list"), {"page": 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["transaksi_list"]), 5)

    def test_transaksi_pagination_dengan_filter_status(self):
        """Test pagination tetap jalan saat filter status aktif"""
        response = self.client.get(
            reverse("transaksi_list"), {"status": "menunggu", "page": 1}
        )
        self.assertEqual(response.status_code, 200)
        # Semua hasil filter status menunggu
        for trx in response.context["transaksi_list"]:
            self.assertEqual(trx.status, "menunggu")

    def test_transaksi_pagination_dengan_filter_search(self):
        """Test pagination tetap jalan saat search"""
        response = self.client.get(
            reverse("transaksi_list"), {"q": "Pelanggan 1", "page": 1}
        )
        self.assertEqual(response.status_code, 200)
        # Semua hasil mengandung kata kunci
        for trx in response.context["transaksi_list"]:
            self.assertIn("Pelanggan 1", trx.pelanggan_nama)

    def test_transaksi_page_invalid(self):
        """Test halaman invalid tetap tampil halaman terakhir"""
        response = self.client.get(reverse("transaksi_list"), {"page": 99999})
        self.assertEqual(response.status_code, 200)

    # ===========================
    # TEST BARANG
    # ===========================

    def test_barang_list_halaman_1(self):
        """Test daftar barang halaman 1 tampil 20 data"""
        response = self.client.get(reverse("barang_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["barang_list"]), 10)

    def test_barang_list_halaman_2(self):
        """Test daftar barang halaman 3 tampil sisa data"""
        response = self.client.get(reverse("barang_list"), {"page": 3})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context["barang_list"]), 0)

    def test_barang_pagination_dengan_filter_kategori(self):
        """Test pagination barang tetap jalan saat filter kategori"""
        response = self.client.get(
            reverse("barang_list"), {"kategori": self.kategori.pk, "page": 1}
        )
        self.assertEqual(response.status_code, 200)
        for barang in response.context["barang_list"]:
            self.assertEqual(barang.kategori, self.kategori)

    def test_barang_pagination_dengan_search(self):
        """Test pagination barang tetap jalan saat search"""
        response = self.client.get(reverse("barang_list"), {"q": "Barang 1", "page": 1})
        self.assertEqual(response.status_code, 200)
        for barang in response.context["barang_list"]:
            self.assertIn("Barang 1", barang.nama)

    # ===========================
    # TEST PELANGGAN
    # ===========================

    def test_pelanggan_list_halaman_1(self):
        """Test daftar pelanggan halaman 1 tampil 20 data"""
        response = self.client.get(reverse("pelanggan_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["pelanggan_list"]), 10)

    def test_pelanggan_list_halaman_2(self):
        """Test daftar pelanggan halaman 3 tampil sisa data"""
        response = self.client.get(reverse("pelanggan_list"), {"page": 3})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.context["pelanggan_list"]), 0)

    def test_pelanggan_pagination_dengan_search(self):
        """Test pagination pelanggan tetap jalan saat search"""
        response = self.client.get(
            reverse("pelanggan_list"), {"q": "Pelanggan Paginasi", "page": 1}
        )
        self.assertEqual(response.status_code, 200)
        for p in response.context["pelanggan_list"]:
            self.assertIn("Pelanggan Paginasi", p.nama)

    def test_pelanggan_page_invalid(self):
        """Test halaman invalid tetap tampil halaman terakhir"""
        response = self.client.get(reverse("pelanggan_list"), {"page": 99999})
        self.assertEqual(response.status_code, 200)


class DiskonTransaksiTest(TestCase):
    """Test fitur diskon nominal di transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_diskon", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_diskon", password="admin123")

        self.barang = Barang.objects.create(
            kode="DK001",
            nama="Barang Diskon Test",
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("100000"),
            kondisi="baik",
        )
        self.pelanggan = Pelanggan.objects.create(nama="Test Diskon", hp="08100000040")

    def test_transaksi_dengan_diskon(self):
        """Test buat transaksi dengan diskon"""
        response = self.client.post(
            reverse("transaksi_create"),
            {
                "pelanggan_id": self.pelanggan.pk,
                "tanggal_sewa": "2026-05-09",
                "tanggal_kembali": "2026-05-10",
                "uang_muka": "50000",
                "diskon": "25000",
                "catatan": "",
                "barang_id": [self.barang.pk],
                "jumlah": ["2"],
                f"kondisi_keluar_{self.barang.pk}": "Baik",
            },
        )
        self.assertEqual(response.status_code, 302)

        transaksi = Transaksi.objects.filter(pelanggan_nama="Test Diskon").first()
        self.assertIsNotNone(transaksi)

        # Total: 100000 x 2 x 1 hari = 200000
        self.assertEqual(transaksi.total_harga, Decimal("200000"))

        # Diskon tersimpan
        self.assertEqual(transaksi.diskon, Decimal("25000"))

        # Sisa bayar: 200000 - 25000 - 50000 = 125000
        self.assertEqual(transaksi.sisa_bayar, Decimal("125000"))

    def test_transaksi_tanpa_diskon(self):
        """Test buat transaksi tanpa diskon"""
        response = self.client.post(
            reverse("transaksi_create"),
            {
                "pelanggan_id": self.pelanggan.pk,
                "tanggal_sewa": "2026-05-09",
                "tanggal_kembali": "2026-05-10",
                "uang_muka": "50000",
                "diskon": "0",
                "catatan": "",
                "barang_id": [self.barang.pk],
                "jumlah": ["1"],
                f"kondisi_keluar_{self.barang.pk}": "Baik",
            },
        )
        self.assertEqual(response.status_code, 302)

        transaksi = Transaksi.objects.filter(pelanggan_nama="Test Diskon").first()

        # Diskon 0
        self.assertEqual(transaksi.diskon, Decimal("0"))

        # Sisa bayar: 100000 - 0 - 50000 = 50000
        self.assertEqual(transaksi.sisa_bayar, Decimal("50000"))

    def test_total_setelah_diskon_property(self):
        """Test property total_setelah_diskon"""
        transaksi = Transaksi.objects.create(
            no_transaksi="SW20260509DK1",
            pelanggan_nama="Test Diskon Property",
            pelanggan_hp="08100000041",
            tanggal_sewa=datetime.date(2026, 5, 9),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("50000"),
            diskon=Decimal("30000"),
            total_harga=Decimal("300000"),
            sisa_bayar=Decimal("220000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )
        # total_setelah_diskon = 300000 - 30000 = 270000
        self.assertEqual(transaksi.total_setelah_diskon, Decimal("270000"))

    def test_diskon_tampil_di_detail(self):
        """Test diskon tampil di halaman detail transaksi"""
        transaksi = Transaksi.objects.create(
            no_transaksi="SW20260509DK2",
            pelanggan_nama="Test Diskon Detail",
            pelanggan_hp="08100000042",
            tanggal_sewa=datetime.date(2026, 5, 9),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("50000"),
            diskon=Decimal("25000"),
            total_harga=Decimal("200000"),
            sisa_bayar=Decimal("125000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )
        response = self.client.get(reverse("transaksi_detail", args=[transaksi.pk]))
        self.assertEqual(response.status_code, 200)
        # Diskon tampil
        self.assertContains(response, "25.000")
        # Sisa bayar tampil
        self.assertContains(response, "125.000")

    def test_diskon_tidak_tampil_jika_nol(self):
        """Test diskon tidak tampil di detail kalau diskon 0"""
        transaksi = Transaksi.objects.create(
            no_transaksi="SW20260509DK3",
            pelanggan_nama="Test Tanpa Diskon",
            pelanggan_hp="08100000043",
            tanggal_sewa=datetime.date(2026, 5, 9),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            diskon=Decimal("0"),
            total_harga=Decimal("100000"),
            sisa_bayar=Decimal("100000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )
        response = self.client.get(reverse("transaksi_detail", args=[transaksi.pk]))
        self.assertEqual(response.status_code, 200)
        # Label diskon tidak tampil
        self.assertNotContains(response, "Total Setelah Diskon")

    def test_sisa_bayar_dengan_diskon_dp(self):
        """Test sisa bayar = total - diskon - dp"""
        total = Decimal("500000")
        diskon = Decimal("50000")
        dp = Decimal("100000")
        expected_sisa = Decimal("350000")

        transaksi = Transaksi.objects.create(
            no_transaksi="SW20260509DK4",
            pelanggan_nama="Test Sisa Bayar",
            pelanggan_hp="08100000044",
            tanggal_sewa=datetime.date(2026, 5, 9),
            tanggal_kembali=datetime.date(2026, 5, 11),
            uang_muka=dp,
            diskon=diskon,
            total_harga=total,
            sisa_bayar=total - diskon - dp,
            status="menunggu",
            dibuat_oleh=self.user,
        )
        self.assertEqual(transaksi.sisa_bayar, expected_sisa)

    def test_diskon_muncul_di_list_transaksi(self):
        """Test transaksi dengan diskon tetap muncul di daftar"""
        Transaksi.objects.create(
            no_transaksi="SW20260509DK5",
            pelanggan_nama="Test Diskon List",
            pelanggan_hp="08100000045",
            tanggal_sewa=datetime.date(2026, 5, 9),
            tanggal_kembali=datetime.date(2026, 5, 10),
            uang_muka=Decimal("0"),
            diskon=Decimal("75000"),
            total_harga=Decimal("300000"),
            sisa_bayar=Decimal("225000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )
        response = self.client.get(reverse("transaksi_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SW20260509DK5")


class InvoiceViewTest(TestCase):
    """Test fitur invoice PDF transaksi"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="admin_invoice", password="admin123"
        )
        UserProfile.objects.create(user=self.user, role="admin")
        self.client.login(username="admin_invoice", password="admin123")

        from apps.inventory.models import Gudang

        self.gudang = Gudang.objects.create(
            nama="Gudang Invoice", alamat="Jl. Invoice No. 1", aktif=True
        )
        self.kategori = Kategori.objects.create(nama="Invoice Test")
        self.barang = Barang.objects.create(
            kode="IV001",
            nama="Barang Invoice",
            kategori=self.kategori,
            gudang=self.gudang,
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("50000"),
            kondisi="baik",
        )
        self.pelanggan = Pelanggan.objects.create(
            nama="Pelanggan Invoice", hp="08100000050", alamat="Jl. Test No. 1"
        )

        # Transaksi dengan diskon
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260510IV1",
            pelanggan=self.pelanggan,
            pelanggan_nama=self.pelanggan.nama,
            pelanggan_hp=self.pelanggan.hp,
            pelanggan_alamat=self.pelanggan.alamat,
            acara="Pernikahan Invoice",
            tanggal_sewa=datetime.date(2026, 5, 10),
            tanggal_kembali=datetime.date(2026, 5, 12),
            uang_muka=Decimal("100000"),
            diskon=Decimal("50000"),
            total_harga=Decimal("500000"),
            sisa_bayar=Decimal("350000"),
            catatan="Catatan invoice test",
            status="menunggu",
            dibuat_oleh=self.user,
        )
        DetailTransaksi.objects.create(
            transaksi=self.transaksi,
            barang=self.barang,
            jumlah=5,
            jumlah_hari=2,
            harga_satuan=Decimal("50000"),
            subtotal=Decimal("500000"),
            kondisi_keluar="Baik",
        )

    def test_invoice_bisa_diakses(self):
        """Test halaman invoice bisa diakses"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transactions/transaksi_invoice.html")

    def test_invoice_redirect_kalau_belum_login(self):
        """Test redirect ke login kalau belum login"""
        self.client.logout()
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_invoice_404_transaksi_tidak_ada(self):
        """Test 404 kalau transaksi tidak ditemukan"""
        response = self.client.get(reverse("transaksi_invoice", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_invoice_tampilkan_no_transaksi(self):
        """Test invoice tampilkan nomor transaksi"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "SW20260510IV1")

    def test_invoice_tampilkan_info_pelanggan(self):
        """Test invoice tampilkan info pelanggan"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Pelanggan Invoice")
        self.assertContains(response, "08100000050")
        self.assertContains(response, "Jl. Test No. 1")

    def test_invoice_tampilkan_acara(self):
        """Test invoice tampilkan nama acara"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Pernikahan Invoice")

    def test_invoice_tampilkan_tanggal(self):
        """Test invoice tampilkan tanggal sewa dan kembali"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "10 Mei 2026")
        self.assertContains(response, "12 Mei 2026")

    def test_invoice_tampilkan_barang(self):
        """Test invoice tampilkan barang yang disewa"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Barang Invoice")
        self.assertContains(response, "IV001")

    def test_invoice_tampilkan_gudang(self):
        """Test invoice tampilkan gudang barang"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Gudang Invoice")

    def test_invoice_tampilkan_jumlah_dan_hari(self):
        """Test invoice tampilkan jumlah dan jumlah hari"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "5")  # jumlah
        self.assertContains(response, "2")  # jumlah hari

    def test_invoice_tampilkan_harga(self):
        """Test invoice tampilkan harga satuan dan subtotal"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "50.000")
        self.assertContains(response, "500.000")

    def test_invoice_tampilkan_diskon(self):
        """Test invoice tampilkan diskon"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "50.000")  # diskon
        self.assertContains(response, "Diskon")

    def test_invoice_tampilkan_uang_muka(self):
        """Test invoice tampilkan uang muka"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "100.000")
        self.assertContains(response, "Uang Muka")

    def test_invoice_tampilkan_sisa_bayar(self):
        """Test invoice tampilkan sisa bayar"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "350.000")
        self.assertContains(response, "SISA BAYAR")

    def test_invoice_tampilkan_catatan(self):
        """Test invoice tampilkan catatan transaksi"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Catatan invoice test")

    def test_invoice_tampilkan_status(self):
        """Test invoice tampilkan status transaksi"""
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertContains(response, "Menunggu")

    def test_invoice_tanpa_diskon(self):
        """Test invoice tampil normal meski tanpa diskon"""
        transaksi_tanpa_diskon = Transaksi.objects.create(
            no_transaksi="SW20260510IV2",
            pelanggan_nama="Test Tanpa Diskon",
            pelanggan_hp="08100000051",
            tanggal_sewa=datetime.date(2026, 5, 10),
            tanggal_kembali=datetime.date(2026, 5, 11),
            uang_muka=Decimal("50000"),
            diskon=Decimal("0"),
            total_harga=Decimal("200000"),
            sisa_bayar=Decimal("150000"),
            status="menunggu",
            dibuat_oleh=self.user,
        )
        response = self.client.get(
            reverse("transaksi_invoice", args=[transaksi_tanpa_diskon.pk])
        )
        self.assertEqual(response.status_code, 200)
        # Label diskon tidak tampil kalau diskon 0
        self.assertNotContains(response, "Total Setelah Diskon")

    def test_invoice_bisa_diakses_karyawan(self):
        """Test karyawan juga bisa akses invoice"""
        karyawan = User.objects.create_user(
            username="karyawan_invoice", password="karyawan123"
        )
        UserProfile.objects.create(user=karyawan, role="karyawan")
        self.client.login(username="karyawan_invoice", password="karyawan123")
        response = self.client.get(
            reverse("transaksi_invoice", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_invoice_semua_status(self):
        """Test invoice bisa diakses di semua status transaksi"""
        for status in ["menunggu", "siap_diambil", "disewa", "selesai"]:
            self.transaksi.status = status
            self.transaksi.save()
            response = self.client.get(
                reverse("transaksi_invoice", args=[self.transaksi.pk])
            )
            self.assertEqual(response.status_code, 200)


class RiwayatPembayaranTest(TestCase):
    """Test fitur riwayat pembayaran / cicilan"""

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username="admin_bayar", password="admin123"
        )
        UserProfile.objects.create(user=self.admin, role="admin")

        self.karyawan = User.objects.create_user(
            username="karyawan_bayar", password="karyawan123"
        )
        UserProfile.objects.create(user=self.karyawan, role="karyawan")

        self.barang = Barang.objects.create(
            kode="PB001",
            nama="Barang Pembayaran",
            stok_total=10,
            stok_tersedia=10,
            harga_sewa=Decimal("50000"),
            kondisi="baik",
        )

        # Transaksi dengan sisa bayar 400000
        self.transaksi = Transaksi.objects.create(
            no_transaksi="SW20260518PB1",
            pelanggan_nama="Test Pembayaran",
            pelanggan_hp="08100000060",
            tanggal_sewa=datetime.date(2026, 5, 18),
            tanggal_kembali=datetime.date(2026, 5, 20),
            uang_muka=Decimal("100000"),
            diskon=Decimal("0"),
            total_harga=Decimal("500000"),
            sisa_bayar=Decimal("400000"),
            status="menunggu",
            dibuat_oleh=self.admin,
        )

    def test_tambah_pembayaran_berhasil(self):
        """Test tambah pembayaran berhasil"""
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {
                "jumlah": "100000",
                "metode": "tunai",
                "keterangan": "Cicilan 1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.transaksi.pembayaran.count(), 1)
        pembayaran = self.transaksi.pembayaran.first()
        self.assertEqual(pembayaran.jumlah, Decimal("100000"))
        self.assertEqual(pembayaran.metode, "tunai")
        self.assertEqual(pembayaran.keterangan, "Cicilan 1")

    def test_tambah_pembayaran_update_sisa_bayar(self):
        """Test sisa bayar berkurang setelah pembayaran"""
        self.client.login(username="admin_bayar", password="admin123")
        self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "150000", "metode": "transfer", "keterangan": ""},
        )
        self.transaksi.refresh_from_db()
        # Sisa bayar: 400000 - 150000 = 250000
        self.assertEqual(self.transaksi.sisa_bayar, Decimal("250000"))

    def test_tambah_pembayaran_melebihi_sisa_gagal(self):
        """Test pembayaran melebihi sisa bayar gagal"""
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "999999", "metode": "tunai", "keterangan": ""},
        )
        self.assertEqual(response.status_code, 302)
        # Tidak ada pembayaran tersimpan
        self.assertEqual(self.transaksi.pembayaran.count(), 0)
        # Sisa bayar tidak berubah
        self.transaksi.refresh_from_db()
        self.assertEqual(self.transaksi.sisa_bayar, Decimal("400000"))

    def test_tambah_pembayaran_jumlah_nol_gagal(self):
        """Test pembayaran dengan jumlah 0 gagal"""
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "0", "metode": "tunai", "keterangan": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.transaksi.pembayaran.count(), 0)

    def test_tambah_pembayaran_negatif_gagal(self):
        """Test pembayaran dengan jumlah negatif gagal"""
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "-50000", "metode": "tunai", "keterangan": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.transaksi.pembayaran.count(), 0)

    def test_transaksi_batal_tidak_bisa_bayar(self):
        """Test transaksi batal tidak bisa tambah pembayaran"""
        self.transaksi.status = "batal"
        self.transaksi.alasan_batal = "Test"
        self.transaksi.save()

        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "100000", "metode": "tunai", "keterangan": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.transaksi.pembayaran.count(), 0)

    def test_property_total_sudah_bayar(self):
        """Test property total_sudah_bayar"""
        from apps.transactions.models import Pembayaran

        # Tambah 2 cicilan
        Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("100000"),
            metode="tunai",
            dicatat_oleh=self.admin,
        )
        Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("150000"),
            metode="transfer",
            dicatat_oleh=self.admin,
        )
        # total_sudah_bayar = uang_muka + cicilan1 + cicilan2
        # = 100000 + 100000 + 150000 = 350000
        self.assertEqual(self.transaksi.total_sudah_bayar, Decimal("350000"))

    def test_property_sisa_bayar_real(self):
        """Test property sisa_bayar_real"""
        from apps.transactions.models import Pembayaran

        Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("200000"),
            metode="tunai",
            dicatat_oleh=self.admin,
        )
        # sisa_bayar_real = total_setelah_diskon - total_sudah_bayar
        # = 500000 - (100000 + 200000) = 200000
        self.assertEqual(self.transaksi.sisa_bayar_real, Decimal("200000"))

    def test_property_sudah_lunas(self):
        """Test property sudah_lunas"""
        from apps.transactions.models import Pembayaran

        # Belum lunas
        self.assertFalse(self.transaksi.sudah_lunas)

        # Tambah pembayaran sampai lunas
        Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("400000"),
            metode="tunai",
            dicatat_oleh=self.admin,
        )
        self.assertTrue(self.transaksi.sudah_lunas)

    def test_lunas_tombol_tambah_bayar_hilang(self):
        """Test tombol tambah bayar hilang saat lunas"""
        from apps.transactions.models import Pembayaran

        Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("400000"),
            metode="tunai",
            dicatat_oleh=self.admin,
        )
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi.pk])
        )

        self.assertEqual(response.status_code, 200)
        # Tombol tambah bayar tidak tampil
        self.assertNotContains(
            response, '<i class="bi bi-plus-lg me-1"></i> Tambah Pembayaran'
        )

    def test_multi_cicilan(self):
        """Test beberapa cicilan berurutan"""
        self.client.login(username="admin_bayar", password="admin123")

        # Cicilan 1
        self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "100000", "metode": "tunai", "keterangan": "Cicilan 1"},
        )
        # Cicilan 2
        self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "150000", "metode": "transfer", "keterangan": "Cicilan 2"},
        )
        # Cicilan 3 - pelunasan
        self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "150000", "metode": "qris", "keterangan": "Pelunasan"},
        )

        self.assertEqual(self.transaksi.pembayaran.count(), 3)
        self.assertTrue(self.transaksi.sudah_lunas)

    def test_hapus_pembayaran_oleh_admin(self):
        """Test admin bisa hapus pembayaran"""
        from apps.transactions.models import Pembayaran

        bayar = Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("100000"),
            metode="tunai",
            dicatat_oleh=self.admin,
        )
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("hapus_pembayaran", args=[self.transaksi.pk, bayar.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.transaksi.pembayaran.count(), 0)

    def test_hapus_pembayaran_oleh_karyawan_gagal(self):
        """Test karyawan tidak bisa hapus pembayaran"""
        from apps.transactions.models import Pembayaran

        bayar = Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("100000"),
            metode="tunai",
            dicatat_oleh=self.admin,
        )
        self.client.login(username="karyawan_bayar", password="karyawan123")
        response = self.client.post(
            reverse("hapus_pembayaran", args=[self.transaksi.pk, bayar.pk])
        )
        self.assertEqual(response.status_code, 302)
        # Pembayaran tidak terhapus
        self.assertEqual(self.transaksi.pembayaran.count(), 1)

    def test_pembayaran_tampil_di_detail(self):
        """Test riwayat pembayaran tampil di detail transaksi"""
        from apps.transactions.models import Pembayaran

        Pembayaran.objects.create(
            transaksi=self.transaksi,
            jumlah=Decimal("100000"),
            metode="tunai",
            keterangan="Cicilan pertama",
            dicatat_oleh=self.admin,
        )
        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.get(
            reverse("transaksi_detail", args=[self.transaksi.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cicilan pertama")
        self.assertContains(response, "Tunai")

    def test_karyawan_bisa_tambah_pembayaran_transaksi_sendiri(self):
        """Test karyawan bisa tambah pembayaran transaksi miliknya"""
        transaksi_karyawan = Transaksi.objects.create(
            no_transaksi="SW20260518PB2",
            pelanggan_nama="Test Karyawan Bayar",
            pelanggan_hp="08100000061",
            tanggal_sewa=datetime.date(2026, 5, 18),
            tanggal_kembali=datetime.date(2026, 5, 20),
            uang_muka=Decimal("50000"),
            diskon=Decimal("0"),
            total_harga=Decimal("300000"),
            sisa_bayar=Decimal("250000"),
            status="menunggu",
            dibuat_oleh=self.karyawan,
        )
        self.client.login(username="karyawan_bayar", password="karyawan123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[transaksi_karyawan.pk]),
            {"jumlah": "100000", "metode": "tunai", "keterangan": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(transaksi_karyawan.pembayaran.count(), 1)

    def test_karyawan_tidak_bisa_tambah_pembayaran_transaksi_orang_lain(self):
        """Test karyawan tidak bisa tambah pembayaran transaksi orang lain"""
        self.client.login(username="karyawan_bayar", password="karyawan123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {"jumlah": "100000", "metode": "tunai", "keterangan": ""},
        )
        self.assertEqual(response.status_code, 302)
        # Pembayaran tidak tersimpan
        self.assertEqual(self.transaksi.pembayaran.count(), 0)

    def test_transaksi_selesai_bisa_tambah_pembayaran(self):
        """Test transaksi selesai tetap bisa tambah pembayaran"""
        self.transaksi.status = "selesai"
        self.transaksi.tanggal_kembali_aktual = datetime.date(2026, 5, 20)
        self.transaksi.save()

        self.client.login(username="admin_bayar", password="admin123")
        response = self.client.post(
            reverse("tambah_pembayaran", args=[self.transaksi.pk]),
            {
                "jumlah": "100000",
                "metode": "tunai",
                "keterangan": "Bayar setelah selesai",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.transaksi.pembayaran.count(), 1)
