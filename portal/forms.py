from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )


class RegisterForm(forms.Form):
    email = forms.EmailField(
        max_length=255,
        widget=forms.EmailInput(attrs={"placeholder": "Email"}),
    )
    first_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "First name"}),
    )
    last_name = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Last name"}),
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )
    password_confirm = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
    )
    role_id = forms.IntegerField(required=False, initial=1)

    def clean(self):
        cleaned = super().clean()
        pw = cleaned.get("password")
        pw2 = cleaned.get("password_confirm")
        if pw and pw2 and pw != pw2:
            raise forms.ValidationError("THE PASSWORDS DO NOT MATCH YOU FOOL.")
        return cleaned
