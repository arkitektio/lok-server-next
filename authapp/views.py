# authapp/views.py
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from authapp.server import server
from authlib.oauth2.rfc6749.errors import OAuth2Error
from django.views.decorators.csrf import csrf_exempt

# use ``server.create_token_response`` to handle token endpoint

@csrf_exempt
@require_http_methods(["POST"])  # we only allow POST for token endpoint
def issue_token(request: HttpRequest) -> HttpResponse:
    return server.create_token_response(request)



class CustomLoginView(LoginView):
    template_name = 'login.html'  # your Tailwind template
    redirect_authenticated_user = True  # Redirect if already logged in 
    success_url = reverse_lazy('home')  # Replace 'home' with your view name

    def get_success_url(self):
        # This uses ?next=... if present; otherwise falls back to success_url
        return self.get_redirect_url() or self.success_url



def logout_view(request):
    logout(request)
    return redirect('login')



@login_required
def home_view(request):
    return render(request, 'home.html', {
        'user': request.user
    })
