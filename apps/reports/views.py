from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.utils import timezone
from apps.transactions.models import Transaksi, DetailTransaksi
from apps.inventory.models import Barang
import datetime


def get_bulan_nama(bulan):
    return datetime.date(2000, bulan, 1).strftime('%B')


@login_required
def laporan_keuangan(request):
    bulan = int(request.GET.get('bulan', timezone.now().month))
    tahun = int(request.GET.get('tahun', timezone.now().year))
    is_print = request.GET.get('print', False)
    is_pdf = request.GET.get('pdf', False)

    transaksi = Transaksi.objects.filter(
        status='selesai',
        tanggal_kembali_aktual__year=tahun,
        tanggal_kembali_aktual__month=bulan
    )

    total_omzet = transaksi.aggregate(total=Sum('total_harga'))['total'] or 0
    total_dp = transaksi.aggregate(total=Sum('uang_muka'))['total'] or 0
    total_sisa = transaksi.aggregate(total=Sum('sisa_bayar'))['total'] or 0
    total_transaksi = transaksi.count()

    months = [(i, datetime.date(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    years = list(range(timezone.now().year - 2, timezone.now().year + 2))

    context = {
        'total_omzet': total_omzet,
        'total_dp': total_dp,
        'total_sisa': total_sisa,
        'total_transaksi': total_transaksi,
        'transaksi_list': transaksi.order_by('tanggal_kembali_aktual'),
        'bulan': bulan,
        'tahun': tahun,
        'bulan_nama': get_bulan_nama(bulan),
        'months': months,
        'years': years,
        'is_print': is_print or is_pdf,
        'generated_at': timezone.now(),
    }

    if is_pdf:
        return render(request, 'reports/keuangan_print.html', context)
    return render(request, 'reports/keuangan.html', context)


@login_required
def laporan_barang(request):
    is_print = request.GET.get('print', False)
    is_pdf = request.GET.get('pdf', False)

    detail = DetailTransaksi.objects.select_related('barang', 'barang__kategori').values(
        'barang__id', 'barang__nama', 'barang__kode', 'barang__kategori__nama'
    ).annotate(
        total_disewa=Sum('jumlah'),
        total_transaksi=Count('transaksi', distinct=True),
        total_pendapatan=Sum('subtotal')
    ).order_by('-total_disewa')

    context = {
        'detail_list': detail,
        'is_print': is_print or is_pdf,
        'generated_at': timezone.now(),
    }

    if is_pdf:
        return render(request, 'reports/barang_print.html', context)
    return render(request, 'reports/barang.html', context)
