from django.contrib.auth.views import LoginView
from django.contrib.auth import logout, login
from django.shortcuts import render, redirect
from .forms import RegistrationForm

class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.role == 'Admin':
            return '/admin/dashboard/'
        elif user.role == 'Entreprise':
            return '/enterprise/dashboard/'
        elif user.role == 'Transporteur':
            return '/transporter/'
        elif user.role == 'Client':
            return '/client/marketplace/'
        return '/'

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Explicitly set the backend to avoid issues on subsequent logins
            user.backend = 'apps.authentication.backends.EmailOrUsernameBackend'
            login(request, user, backend=user.backend)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('login')

