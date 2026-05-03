from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Pelanggan
from .forms import PelangganForm


@login_required
def pelanggan_list(request):
    q = request.GET.get('q', '')
    pelanggan = Pelanggan.objects.all()
    if q:
        pelanggan = pelanggan.filter(
            Q(nama__icontains=q) | Q(hp__icontains=q)
        )
    return render(request, 'pelanggan/pelanggan_list.html', {
        'pelanggan_list': pelanggan,
        'q': q,
    })


@login_required
def pelanggan_detail(request, pk):
    pelanggan = get_object_or_404(Pelanggan, pk=pk)
    transaksi = pelanggan.transaksi_set.order_by('-created_at')[:10]
    return render(request, 'pelanggan/pelanggan_detail.html', {
        'pelanggan': pelanggan,
        'transaksi': transaksi,
    })


@login_required
def pelanggan_create(request):
    form = PelangganForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pelanggan = form.save()
        messages.success(request, f'Pelanggan "{pelanggan.nama}" berhasil ditambahkan.')
        # Kalau dari modal/ajax di halaman transaksi
        if request.GET.get('next') == 'transaksi':
            return redirect('transaksi_create')
        return redirect('pelanggan_list')
    return render(request, 'pelanggan/pelanggan_form.html', {
        'form': form,
        'title': 'Tambah Pelanggan Baru',
    })


@login_required
def pelanggan_edit(request, pk):
    pelanggan = get_object_or_404(Pelanggan, pk=pk)
    form = PelangganForm(request.POST or None, instance=pelanggan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Data pelanggan "{pelanggan.nama}" berhasil diperbarui.')
        return redirect('pelanggan_list')
    return render(request, 'pelanggan/pelanggan_form.html', {
        'form': form,
        'title': 'Edit Pelanggan',
        'pelanggan': pelanggan,
    })


@login_required
def pelanggan_delete(request, pk):
    pelanggan = get_object_or_404(Pelanggan, pk=pk)
    if request.method == 'POST':
        pelanggan.delete()
        messages.success(request, 'Pelanggan berhasil dihapus.')
        return redirect('pelanggan_list')
    return render(request, 'pelanggan/pelanggan_confirm_delete.html', {
        'pelanggan': pelanggan,
    })


@login_required
def pelanggan_search_api(request):
    """API endpoint untuk autocomplete pencarian pelanggan di form transaksi"""
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'results': []})
    pelanggan = Pelanggan.objects.filter(
        Q(nama__icontains=q) | Q(hp__icontains=q)
    )[:10]
    results = [
        {
            'id': p.pk,
            'nama': p.nama,
            'hp': p.hp,
            'alamat': p.alamat,
        }
        for p in pelanggan
    ]
    return JsonResponse({'results': results})
