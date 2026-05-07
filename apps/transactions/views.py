from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from .models import Transaksi, DetailTransaksi
from apps.inventory.models import Barang
from apps.pelanggan.models import Pelanggan
import datetime
from decimal import Decimal

def cek_akses_transaksi(user, transaksi):
    """
    Cek apakah user punya akses untuk proses transaksi.
    Admin bisa akses semua, karyawan hanya transaksi sendiri.
    """
    if user.profile.role == 'admin':
        return True
    return transaksi.dibuat_oleh == user


def generate_no_transaksi():
    today = datetime.date.today()
    prefix = f"SW{today.strftime('%Y%m%d')}"
    last = Transaksi.objects.filter(no_transaksi__startswith=prefix).count()
    return f"{prefix}{str(last + 1).zfill(3)}"


def hitung_jumlah_hari(tanggal_sewa, tanggal_kembali):
    try:
        tgl_sewa = datetime.datetime.strptime(str(tanggal_sewa), '%Y-%m-%d').date()
        tgl_kembali = datetime.datetime.strptime(str(tanggal_kembali), '%Y-%m-%d').date()
        selisih = (tgl_kembali - tgl_sewa).days
        return max(selisih, 1)
    except:
        return 1


@login_required
def transaksi_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    tanggal = request.GET.get('tanggal', '')
    pengguna_id = request.GET.get('pengguna', '')

    transaksi = Transaksi.objects.select_related('pelanggan', 'dibuat_oleh').all()
    if q:
        transaksi = transaksi.filter(
            Q(no_transaksi__icontains=q) | Q(pelanggan_nama__icontains=q)
        )
    if status:
        transaksi = transaksi.filter(status=status)
    if tanggal:
        transaksi = transaksi.filter(tanggal_sewa=tanggal)
    if pengguna_id:
        transaksi = transaksi.filter(dibuat_oleh_id=pengguna_id)

    from django.contrib.auth.models import User
    pengguna_list = User.objects.filter(
        transaksi__isnull=False
    ).distinct().order_by('first_name')

    return render(request, 'transactions/transaksi_list.html', {
        'transaksi_list': transaksi,
        'q': q,
        'selected_status': status,
        'tanggal': tanggal,
        'pengguna_list': pengguna_list,
        'selected_pengguna': pengguna_id,
    })


@login_required
def transaksi_detail(request, pk):
    transaksi = get_object_or_404(Transaksi, pk=pk)
    detail = transaksi.detail.select_related('barang')
    return render(request, 'transactions/transaksi_detail.html', {
        'transaksi': transaksi,
        'detail': detail,
    })


@login_required
def transaksi_create(request):
    barang_list = Barang.objects.filter(stok_tersedia__gt=0, kondisi='baik')
    pelanggan_list = Pelanggan.objects.all().order_by('nama')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                no_transaksi = generate_no_transaksi()
                uang_muka_raw = request.POST.get('uang_muka', '0') or '0'
                uang_muka = Decimal(str(uang_muka_raw))

                tanggal_sewa = request.POST['tanggal_sewa']
                tanggal_kembali = request.POST['tanggal_kembali']
                jumlah_hari = hitung_jumlah_hari(tanggal_sewa, tanggal_kembali)

                pelanggan_id = request.POST.get('pelanggan_id', '')
                pelanggan_obj = None

                if pelanggan_id:
                    pelanggan_obj = Pelanggan.objects.get(pk=int(pelanggan_id))
                    nama = pelanggan_obj.nama
                    hp = pelanggan_obj.hp
                    alamat = pelanggan_obj.alamat
                else:
                    nama = request.POST.get('pelanggan_nama', '')
                    hp = request.POST.get('pelanggan_hp', '')
                    alamat = request.POST.get('pelanggan_alamat', '')
                    if nama and hp:
                        pelanggan_obj, created = Pelanggan.objects.get_or_create(
                            hp=hp,
                            defaults={'nama': nama, 'alamat': alamat}
                        )
                        if not created:
                            pelanggan_obj.nama = nama
                            pelanggan_obj.alamat = alamat
                            pelanggan_obj.save()

                trx = Transaksi.objects.create(
                    no_transaksi=no_transaksi,
                    pelanggan=pelanggan_obj,
                    pelanggan_nama=nama,
                    pelanggan_hp=hp,
                    pelanggan_alamat=alamat,
                    acara=request.POST.get('acara', ''),
                    tanggal_sewa=tanggal_sewa,
                    tanggal_kembali=tanggal_kembali,
                    uang_muka=uang_muka,
                    catatan=request.POST.get('catatan', ''),
                    dibuat_oleh=request.user,
                    total_harga=Decimal('0'),
                    status='menunggu',
                )

                barang_ids = request.POST.getlist('barang_id')
                jumlah_list = request.POST.getlist('jumlah')
                total = Decimal('0')

                for b_id, jml in zip(barang_ids, jumlah_list):
                    if not b_id or not jml:
                        continue
                    barang = Barang.objects.select_for_update().get(pk=int(b_id))
                    jml = int(jml)
                    if jml > barang.stok_tersedia:
                        raise ValueError(f"Stok {barang.nama} tidak mencukupi (tersedia: {barang.stok_tersedia})")

                    harga_satuan = Decimal(str(barang.harga_sewa))
                    subtotal = harga_satuan * Decimal(str(jml)) * Decimal(str(jumlah_hari))

                    DetailTransaksi.objects.create(
                        transaksi=trx,
                        barang=barang,
                        jumlah=jml,
                        jumlah_hari=jumlah_hari,
                        harga_satuan=harga_satuan,
                        subtotal=subtotal,
                        kondisi_keluar=request.POST.get(f'kondisi_keluar_{b_id}', 'Baik')
                    )
                    total += subtotal
                    # Stok langsung dikunci saat menunggu
                    barang.stok_tersedia -= jml
                    barang.save()

                trx.total_harga = total
                trx.sisa_bayar = total - uang_muka
                trx.save()

                if pelanggan_obj:
                    pelanggan_obj.total_transaksi = pelanggan_obj.transaksi_set.count()
                    pelanggan_obj.save()

                messages.success(request, f'Transaksi {no_transaksi} berhasil dibuat.')
                return redirect('transaksi_detail', pk=trx.pk)

        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Gagal membuat transaksi: {str(e)}')

    return render(request, 'transactions/transaksi_form.html', {
        'barang_list': barang_list,
        'pelanggan_list': pelanggan_list,
        'today': timezone.now().date(),
    })


@login_required
def transaksi_siap_diambil(request, pk):
    transaksi = get_object_or_404(Transaksi, pk=pk, status='menunggu')

    # Cek akses
    if not cek_akses_transaksi(request.user, transaksi):
        messages.error(request, 'Anda tidak memiliki akses untuk memproses transaksi ini.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    if request.method == 'POST':
        transaksi.status = 'siap_diambil'
        transaksi.save()
        messages.success(request, f'Transaksi {transaksi.no_transaksi} siap diambil.')
        return redirect('transaksi_detail', pk=transaksi.pk)
    return render(request, 'transactions/transaksi_konfirmasi.html', {
        'transaksi': transaksi,
        'aksi': 'siap_diambil',
        'judul': 'Konfirmasi Siap Diambil',
        'pesan': 'Barang sudah disiapkan dan siap diambil oleh pelanggan?',
        'btn_label': 'Ya, Siap Diambil',
        'btn_color': '#20948A',
    })


@login_required
def transaksi_disewa(request, pk):
    transaksi = get_object_or_404(Transaksi, pk=pk, status='siap_diambil')

    # Cek akses
    if not cek_akses_transaksi(request.user, transaksi):
        messages.error(request, 'Anda tidak memiliki akses untuk memproses transaksi ini.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    if request.method == 'POST':
        transaksi.status = 'disewa'
        transaksi.save()
        messages.success(request, f'Transaksi {transaksi.no_transaksi} sedang disewa.')
        return redirect('transaksi_detail', pk=transaksi.pk)
    return render(request, 'transactions/transaksi_konfirmasi.html', {
        'transaksi': transaksi,
        'aksi': 'disewa',
        'judul': 'Konfirmasi Barang Keluar',
        'pesan': 'Barang sudah diambil dan keluar dari gudang?',
        'btn_label': 'Ya, Barang Sudah Keluar',
        'btn_color': '#C9A84C',
    })


@login_required
def transaksi_kembali(request, pk):
    transaksi = get_object_or_404(Transaksi, pk=pk, status='disewa')

    # Cek akses
    if not cek_akses_transaksi(request.user, transaksi):
        messages.error(request, 'Anda tidak memiliki akses untuk memproses transaksi ini.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    if request.method == 'POST':
        with transaction.atomic():
            for detail in transaksi.detail.select_related('barang'):
                kondisi = request.POST.get(f'kondisi_kembali_{detail.pk}', 'Baik')
                detail.kondisi_kembali = kondisi
                detail.save()
                detail.barang.stok_tersedia += detail.jumlah
                detail.barang.save()
            transaksi.status = 'selesai'
            transaksi.tanggal_kembali_aktual = timezone.now().date()
            transaksi.save()
        messages.success(request, f'Transaksi {transaksi.no_transaksi} selesai.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    return render(request, 'transactions/transaksi_kembali.html', {
        'transaksi': transaksi,
        'detail': transaksi.detail.select_related('barang'),
    })


@login_required
def transaksi_batal(request, pk):
    transaksi = get_object_or_404(
        Transaksi, pk=pk, status__in=['menunggu', 'siap_diambil']
    )

    # Cek akses
    if not cek_akses_transaksi(request.user, transaksi):
        messages.error(request, 'Anda tidak memiliki akses untuk membatalkan transaksi ini.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    if request.method == 'POST':
        alasan = request.POST.get('alasan_batal', '').strip()
        if not alasan:
            messages.error(request, 'Alasan pembatalan wajib diisi.')
            return render(request, 'transactions/transaksi_batal.html', {
                'transaksi': transaksi,
                'error': 'Alasan pembatalan wajib diisi.'
            })

        with transaction.atomic():
            for detail in transaksi.detail.select_related('barang'):
                detail.barang.stok_tersedia += detail.jumlah
                detail.barang.save()
            transaksi.status = 'batal'
            transaksi.alasan_batal = alasan
            transaksi.dibatalkan_oleh = request.user
            transaksi.dibatalkan_at = timezone.now()
            transaksi.save()

        messages.success(request, f'Transaksi {transaksi.no_transaksi} dibatalkan.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    return render(request, 'transactions/transaksi_batal.html', {
        'transaksi': transaksi,
    })


@login_required
def jadwal_view(request):
    today = timezone.now().date()

    menunggu = Transaksi.objects.filter(status='menunggu').order_by('tanggal_sewa')
    siap_diambil = Transaksi.objects.filter(status='siap_diambil').order_by('tanggal_sewa')
    disewa = Transaksi.objects.filter(status='disewa').order_by('tanggal_kembali')
    terlambat = disewa.filter(tanggal_kembali__lt=today)
    kembali_hari_ini = disewa.filter(tanggal_kembali=today)
    akan_datang = disewa.filter(tanggal_kembali__gt=today)

    return render(request, 'transactions/jadwal.html', {
        'menunggu': menunggu,
        'siap_diambil': siap_diambil,
        'terlambat': terlambat,
        'kembali_hari_ini': kembali_hari_ini,
        'akan_datang': akan_datang,
        'today': today,
    })