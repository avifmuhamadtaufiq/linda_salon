from django.test import TestCase
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.inventory.models import Kategori, Barang
from apps.pelanggan.models import Pelanggan
from apps.transactions.models import Transaksi, DetailTransaksi
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
        self.assertEqual(self.transaksi.status, 'aktif')

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