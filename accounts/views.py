from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
from .models import User
from .forms import CandidateRegistrationForm, EmployerRegistrationForm, LoginForm

def home(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.CANDIDATE:
            return redirect('candidate_dashboard')
        elif request.user.role == User.Role.EMPLOYER:
            return redirect('employer_dashboard')
    return render(request, 'home.html')

def role_selection(request, action):
    # action is either 'login' or 'register'
    return render(request, 'role_selection.html', {'action': action})

def register(request, role):
    if request.user.is_authenticated:
        return redirect('home')
        
    role_map = {
        'candidate': User.Role.CANDIDATE,
        'employer': User.Role.EMPLOYER
    }
    
    if role not in role_map:
        return redirect('role_selection', action='register')
        
    FormClass = CandidateRegistrationForm if role == 'candidate' else EmployerRegistrationForm
    
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = role_map[role]
            user.totp_secret = pyotp.random_base32()
            user.save()
            request.session['totp_setup_user_id'] = user.id
            return redirect('totp_setup')
    else:
        form = FormClass()
        
    return render(request, 'register.html', {'form': form, 'role': role})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                if user.role == User.Role.ADMIN:
                    form.add_error(None, 'Administrators must use the secure portal.')
                    return render(request, 'login.html', {'form': form})
                if user.is_totp_enabled:
                    request.session['pre_login_user_id'] = user.id
                    return redirect('totp_verify')
                elif user.totp_secret:
                    request.session['totp_setup_user_id'] = user.id
                    return redirect('totp_setup')
                else:
                    user.totp_secret = pyotp.random_base32()
                    user.save()
                    request.session['totp_setup_user_id'] = user.id
                    return redirect('totp_setup')
            else:
                form.add_error(None, 'Invalid credentials')
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

def totp_setup(request):
    user_id = request.session.get('totp_setup_user_id')
    if not user_id:
        return redirect('home')
    
    user = User.objects.get(id=user_id)
    
    if request.method == 'POST':
        token = request.POST.get('token', '').replace(' ', '').strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token):
            user.is_totp_enabled = True
            user.save()
            login(request, user)
            del request.session['totp_setup_user_id']
            return redirect(f'{user.role.lower()}_dashboard')
        else:
            messages.error(request, 'Invalid TOTP code. Please try again.')
            
    import base64
    totp_uri = pyotp.totp.TOTP(user.totp_secret).provisioning_uri(name=user.email, issuer_name='JobPortal')
    img = qrcode.make(totp_uri)
    stream = BytesIO()
    img.save(stream, format='PNG')
    b64_img = base64.b64encode(stream.getvalue()).decode('utf-8')
    qr_data = f"data:image/png;base64,{b64_img}"
    
    return render(request, 'totp_setup.html', {'qr_data': qr_data, 'secret': user.totp_secret})

def totp_verify(request):
    user_id = request.session.get('pre_login_user_id')
    if not user_id:
        return redirect('home')

    user = User.objects.get(id=user_id)

    if request.method == 'POST':
        token = request.POST.get('token', '').replace(' ', '').strip()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(token):
            login(request, user)
            del request.session['pre_login_user_id']
            return redirect(f'{user.role.lower()}_dashboard')
        else:
            messages.error(request, 'Invalid TOTP code. Please try again.')

    return render(request, 'totp_verify.html')

@login_required
def candidate_dashboard(request):
    if request.user.role != User.Role.CANDIDATE:
        return redirect('home')
    return render(request, 'candidate_dashboard.html')

@login_required
def employer_dashboard(request):
    if request.user.role != User.Role.EMPLOYER:
        return redirect('home')
    return render(request, 'employer_dashboard.html')

def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.Role.ADMIN:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_login(request):
    if request.user.is_authenticated and request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None and user.role == User.Role.ADMIN:
                if user.is_totp_enabled:
                    request.session['pre_login_user_id'] = user.id
                    return redirect('totp_verify')
                elif user.totp_secret:
                    request.session['totp_setup_user_id'] = user.id
                    return redirect('totp_setup')
                else:
                    user.totp_secret = pyotp.random_base32()
                    user.save()
                    request.session['totp_setup_user_id'] = user.id
                    return redirect('totp_setup')
            else:
                form.add_error(None, 'Invalid admin credentials')
    else:
        form = LoginForm()

    return render(request, 'admin/admin_login.html', {'form': form})

@admin_required
def admin_dashboard(request):
    from .models import SecurityAuditLog
    users = User.objects.all().order_by('-date_joined')
    audit_logs = SecurityAuditLog.objects.all()[:50]
    return render(request, 'admin/admin_dashboard.html', {'users': users, 'audit_logs': audit_logs})

@admin_required
def moderate_user(request, user_id, action):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        if target_user.role == User.Role.ADMIN:
            messages.error(request, "Cannot moderate other administrators.")
            return redirect('admin_dashboard')
            
        if action == 'suspend':
            target_user.is_active = not target_user.is_active
            target_user.save()
            status = 'suspended' if not target_user.is_active else 'reactivated'
            messages.success(request, f"User {target_user.email} has been {status}.")
        elif action == 'delete':
            target_user.delete()
            messages.success(request, f"User has been permanently deleted.")
            
    return redirect('admin_dashboard')
