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


def generate_no_transaksi():
    today = datetime.date.today()
    prefix = f"SW{today.strftime('%Y%m%d')}"
    last = Transaksi.objects.filter(no_transaksi__startswith=prefix).count()
    return f"{prefix}{str(last + 1).zfill(3)}"


def hitung_jumlah_hari(tanggal_sewa, tanggal_kembali):
    """Hitung jumlah hari antara tanggal sewa dan kembali, minimal 1 hari"""
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

    transaksi = Transaksi.objects.select_related('pelanggan').all()
    if q:
        transaksi = transaksi.filter(
            Q(no_transaksi__icontains=q) | Q(pelanggan_nama__icontains=q)
        )
    if status:
        transaksi = transaksi.filter(status=status)
    if tanggal:
        transaksi = transaksi.filter(tanggal_sewa=tanggal)

    return render(request, 'transactions/transaksi_list.html', {
        'transaksi_list': transaksi,
        'q': q,
        'selected_status': status,
        'tanggal': tanggal,
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

                # Hitung otomatis jumlah hari
                jumlah_hari = hitung_jumlah_hari(tanggal_sewa, tanggal_kembali)

                # Cek pelanggan
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
                    # Harga = harga/hari x jumlah barang x jumlah hari
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
                    barang.stok_tersedia -= jml
                    barang.save()

                trx.total_harga = total
                trx.sisa_bayar = total - uang_muka
                trx.save()

                if pelanggan_obj:
                    pelanggan_obj.total_transaksi = pelanggan_obj.transaksi_set.count()
                    pelanggan_obj.save()

                messages.success(request, f'Transaksi {no_transaksi} berhasil dibuat. ({jumlah_hari} hari sewa)')
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
def transaksi_kembali(request, pk):
    transaksi = get_object_or_404(Transaksi, pk=pk, status='aktif')
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
        messages.success(request, f'Pengembalian transaksi {transaksi.no_transaksi} berhasil dicatat.')
        return redirect('transaksi_detail', pk=transaksi.pk)

    return render(request, 'transactions/transaksi_kembali.html', {
        'transaksi': transaksi,
        'detail': transaksi.detail.select_related('barang'),
    })


@login_required
def jadwal_view(request):
    today = timezone.now().date()
    transaksi_aktif = Transaksi.objects.filter(status='aktif').order_by('tanggal_kembali')
    pengembalian_terlambat = transaksi_aktif.filter(tanggal_kembali__lt=today)
    pengembalian_hari_ini = transaksi_aktif.filter(tanggal_kembali=today)
    akan_datang = transaksi_aktif.filter(tanggal_kembali__gt=today)

    return render(request, 'transactions/jadwal.html', {
        'pengembalian_terlambat': pengembalian_terlambat,
        'pengembalian_hari_ini': pengembalian_hari_ini,
        'akan_datang': akan_datang,
        'today': today,
    })
