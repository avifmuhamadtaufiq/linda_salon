from django import forms


class LoginForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Username"}
        ),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Password"}
        ),
    )


class UserCreateForm(forms.Form):
    ROLE_CHOICES = [("admin", "Admin"), ("karyawan", "Karyawan")]

    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        label="Nama Lengkap",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    role = forms.ChoiceField(
        label="Role",
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    phone = forms.CharField(
        label="No. HP",
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
