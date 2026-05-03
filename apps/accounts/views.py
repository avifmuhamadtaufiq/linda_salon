from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from .forms import LoginForm, UserCreateForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Username atau password salah.')
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def user_list(request):
    if request.user.profile.role != 'admin':
        messages.error(request, 'Anda tidak memiliki akses.')
        return redirect('dashboard')
    users = User.objects.select_related('profile').all().order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def user_create(request):
    if request.user.profile.role != 'admin':
        return redirect('dashboard')
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            password=form.cleaned_data['password'],
            first_name=form.cleaned_data['first_name'],
            email=form.cleaned_data.get('email', '')
        )
        UserProfile.objects.create(user=user, role=form.cleaned_data['role'], phone=form.cleaned_data.get('phone', ''))
        messages.success(request, f'Pengguna {user.username} berhasil dibuat.')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Tambah Pengguna'})

@login_required
def user_delete(request, pk):
    if request.user.profile.role != 'admin':
        return redirect('dashboard')
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Pengguna berhasil dihapus.')
        return redirect('user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'object': user})
