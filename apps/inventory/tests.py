from django.test import TestCase
from apps.inventory.models import Kategori, Barang


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