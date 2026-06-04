from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'role', 'company_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclude 'Admin' from role choices for registration
        self.fields['role'].choices = [
            choice for choice in User.ROLE_CHOICES if choice[0] != 'Admin'
        ]
