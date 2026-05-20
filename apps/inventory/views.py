from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Barang, Kategori
from .forms import BarangForm, KategoriForm
from .models import Gudang
from apps.transactions.models import Transaksi


@login_required
def dashboard(request):
    total_barang = Barang.objects.count()
    total_stok = Barang.objects.aggregate(total=Sum('stok_total'))['total'] or 0
    total_tersedia = Barang.objects.aggregate(total=Sum('stok_tersedia'))['total'] or 0
    total_disewa = total_stok - total_tersedia

    today = timezone.now().date()

    # Hitung per status
    trx_menunggu = Transaksi.objects.filter(status='menunggu').count()
    trx_siap_diambil = Transaksi.objects.filter(status='siap_diambil').count()
    trx_disewa = Transaksi.objects.filter(status='disewa').count()
    trx_selesai_hari_ini = Transaksi.objects.filter(
        status='selesai',
        tanggal_kembali_aktual=today
    ).count()
    pengembalian_hari_ini = Transaksi.objects.filter(
        status='disewa',
        tanggal_kembali=today
    ).count()

    transaksi_terbaru = Transaksi.objects.select_related(
        'pelanggan', 'dibuat_oleh'
    ).order_by('-created_at')[:5]
    barang_low_stock = Barang.objects.filter(
        stok_tersedia=0, stok_total__gt=0
    )

    context = {
        'total_barang': total_barang,
        'total_stok': total_stok,
        'total_tersedia': total_tersedia,
        'total_disewa': total_disewa,
        'trx_menunggu': trx_menunggu,
        'trx_siap_diambil': trx_siap_diambil,
        'trx_disewa': trx_disewa,
        'trx_selesai_hari_ini': trx_selesai_hari_ini,
        'pengembalian_hari_ini': pengembalian_hari_ini,
        'transaksi_terbaru': transaksi_terbaru,
        'barang_low_stock': barang_low_stock,
    }
    return render(request, 'inventory/dashboard.html', context)


@login_required
def barang_list(request):
    q = request.GET.get('q', '')
    kategori_id = request.GET.get('kategori', '')
    kondisi = request.GET.get('kondisi', '')
    gudang_id = request.GET.get('gudang', '')

    barang = Barang.objects.select_related('kategori', 'gudang').all()
    if q:
        barang = barang.filter(Q(nama__icontains=q) | Q(kode__icontains=q))
    if kategori_id:
        barang = barang.filter(kategori_id=kategori_id)
    if kondisi:
        barang = barang.filter(kondisi=kondisi)
    if gudang_id:
        barang = barang.filter(gudang_id=gudang_id)

    kategori_list = Kategori.objects.all()
    gudang_list = Gudang.objects.filter(aktif=True)

    # Pagination
    paginator = Paginator(barang, 10)
    page = request.GET.get('page', 1)
    barang_page = paginator.get_page(page)

    return render(request, 'inventory/barang_list.html', {
        'barang_list': barang_page,
        'page_obj': barang_page,
        'kategori_list': kategori_list,
        'gudang_list': gudang_list,
        'q': q,
        'selected_kategori': kategori_id,
        'selected_kondisi': kondisi,
        'selected_gudang': gudang_id,
    })
    

@login_required
def barang_detail(request, pk):
    barang = get_object_or_404(Barang, pk=pk)
    riwayat = barang.detail_transaksi.select_related('transaksi').order_by('-transaksi__created_at')[:10]
    return render(request, 'inventory/barang_detail.html', {'barang': barang, 'riwayat': riwayat})


@login_required
def barang_create(request):
    form = BarangForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        barang = form.save()
        messages.success(request, f'Barang "{barang.nama}" berhasil ditambahkan.')
        return redirect('barang_list')
    return render(request, 'inventory/barang_form.html', {'form': form, 'title': 'Tambah Barang'})


@login_required
def barang_edit(request, pk):
    barang = get_object_or_404(Barang, pk=pk)
    form = BarangForm(request.POST or None, request.FILES or None, instance=barang)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Barang "{barang.nama}" berhasil diperbarui.')
        return redirect('barang_list')
    return render(request, 'inventory/barang_form.html', {'form': form, 'title': 'Edit Barang', 'barang': barang})


@login_required
def barang_delete(request, pk):
    barang = get_object_or_404(Barang, pk=pk)
    if request.method == 'POST':
        barang.delete()
        messages.success(request, 'Barang berhasil dihapus.')
        return redirect('barang_list')
    return render(request, 'inventory/barang_confirm_delete.html', {'barang': barang})


@login_required
def kategori_list(request):
    kategori = Kategori.objects.all()
    return render(request, 'inventory/kategori_list.html', {'kategori_list': kategori})


@login_required
def kategori_create(request):
    form = KategoriForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kategori berhasil ditambahkan.')
        return redirect('kategori_list')
    return render(request, 'inventory/kategori_form.html', {'form': form, 'title': 'Tambah Kategori'})


@login_required
def gudang_list(request):
    gudang = Gudang.objects.all()
    return render(request, 'inventory/gudang_list.html', {
        'gudang_list': gudang
    })


@login_required
def gudang_create(request):
    if request.method == 'POST':
        nama = request.POST.get('nama', '')
        alamat = request.POST.get('alamat', '')
        keterangan = request.POST.get('keterangan', '')
        if nama:
            Gudang.objects.create(
                nama=nama,
                alamat=alamat,
                keterangan=keterangan
            )
            messages.success(request, f'Gudang "{nama}" berhasil ditambahkan.')
            return redirect('gudang_list')
        messages.error(request, 'Nama gudang tidak boleh kosong.')
    return render(request, 'inventory/gudang_form.html', {
        'title': 'Tambah Gudang'
    })


@login_required
def gudang_edit(request, pk):
    gudang = get_object_or_404(Gudang, pk=pk)
    if request.method == 'POST':
        gudang.nama = request.POST.get('nama', gudang.nama)
        gudang.alamat = request.POST.get('alamat', gudang.alamat)
        gudang.keterangan = request.POST.get('keterangan', gudang.keterangan)
        gudang.aktif = request.POST.get('aktif') == 'on'
        gudang.save()
        messages.success(request, f'Gudang "{gudang.nama}" berhasil diperbarui.')
        return redirect('gudang_list')
    return render(request, 'inventory/gudang_form.html', {
        'title': 'Edit Gudang',
        'gudang': gudang
    })


@login_required
def gudang_delete(request, pk):
    gudang = get_object_or_404(Gudang, pk=pk)
    if request.method == 'POST':
        gudang.delete()
        messages.success(request, 'Gudang berhasil dihapus.')
        return redirect('gudang_list')
    return render(request, 'inventory/gudang_confirm_delete.html', {
        'gudang': gudang
    })