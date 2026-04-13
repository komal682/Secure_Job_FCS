from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import pyotp
import qrcode
import qrcode.image.svg
from io import BytesIO
from django.core.cache import cache
from .models import User, SecurityAuditLog
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

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

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
            
            # Generate PKI Keypair
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            raw_password = form.cleaned_data['password'].encode()
            
            pem_private = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.BestAvailableEncryption(raw_password)
            )
            pem_public = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            user.private_key_encrypted = pem_private.decode('utf-8')
            user.public_key = pem_public.decode('utf-8')
            
            user.save()
            request.session['totp_setup_user_id'] = user.id
            return redirect('totp_setup')
    else:
        form = FormClass()
        
    return render(request, 'register.html', {'form': form, 'role': role})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    cache_key = f'bf_lock_{ip}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= 5:
        form = LoginForm()
        form.add_error(None, 'SECURITY LOCK: IP blocked for 15 minutes due to brute force.')
        return render(request, 'login.html', {'form': form})

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None:
                cache.delete(cache_key)
                request.session['pki_passphrase'] = password
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
                attempts += 1
                cache.set(cache_key, attempts, timeout=900)
                if attempts == 5:
                    SecurityAuditLog.objects.create(action_type="BRUTE_FORCE_LOCKOUT", ip_address=ip, details="5 failed attempts.")
                    form.add_error(None, 'SECURITY LOCK: IP blocked for 15 minutes due to brute force.')
                else:
                    form.add_error(None, f'Invalid credentials. Attempt {attempts}/5.')
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
            request.session.pop('totp_setup_user_id', None)
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
            request.session.pop('pre_login_user_id', None)
            return redirect(f'{user.role.lower()}_dashboard')
        else:
            messages.error(request, 'Invalid TOTP code. Please try again.')

    return render(request, 'totp_verify.html')

from django.http import JsonResponse
import json

@login_required
def api_get_profile(request):
    if request.user.role != User.Role.CANDIDATE:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    profile, _ = CandidateProfile.objects.get_or_create(candidate=request.user)
    educations = profile.educations.all()
    
    edu_list = [{
        'id': e.id,
        'school': e.school,
        'degree': e.degree,
        'field_of_study': e.field_of_study,
        'start_month': e.start_month,
        'start_year': e.start_year,
        'end_month': e.end_month,
        'end_year': e.end_year,
        'grade': e.grade
    } for e in educations]
    
    return JsonResponse({
        'summary': profile.summary,
        'skills': profile.skills,
        'visibility': profile.visibility,
        'opt_out_view_tracking': profile.opt_out_view_tracking,
        'educations': edu_list
    })

@login_required
def api_update_profile(request):
    """Updates summary, skills, or visibility fields."""
    if request.user.role != User.Role.CANDIDATE or request.method != 'POST':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    try:
        data = json.loads(request.body)
        profile = request.user.candidate_profile
        
        if 'summary' in data:
            profile.summary = data['summary']
        if 'skills' in data:
            profile.skills = data['skills']
        if 'visibility' in data:
            profile.visibility = data['visibility']
            
        profile.save()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def api_education(request, edu_id=None):
    if request.user.role != User.Role.CANDIDATE:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    profile = request.user.candidate_profile
    
    if request.method == 'POST':
        data = json.loads(request.body)
        edu = Education.objects.create(
            profile=profile,
            school=data.get('school', ''),
            degree=data.get('degree', ''),
            field_of_study=data.get('field_of_study', ''),
            start_month=data.get('start_month', ''),
            start_year=data.get('start_year', ''),
            end_month=data.get('end_month', ''),
            end_year=data.get('end_year', ''),
            grade=data.get('grade', '')
        )
        return JsonResponse({'status': 'success', 'id': edu.id})
        
    elif request.method == 'PUT':
        if not edu_id:
            return JsonResponse({'error': 'Missing ID'}, status=400)
        data = json.loads(request.body)
        edu = get_object_or_404(Education, id=edu_id, profile=profile)
        edu.school = data.get('school', edu.school)
        edu.degree = data.get('degree', edu.degree)
        edu.field_of_study = data.get('field_of_study', edu.field_of_study)
        edu.start_month = data.get('start_month', edu.start_month)
        edu.start_year = data.get('start_year', edu.start_year)
        edu.end_month = data.get('end_month', edu.end_month)
        edu.end_year = data.get('end_year', edu.end_year)
        edu.grade = data.get('grade', edu.grade)
        edu.save()
        return JsonResponse({'status': 'success'})
        
    elif request.method == 'DELETE':
        if not edu_id:
            return JsonResponse({'error': 'Missing ID'}, status=400)
        edu = get_object_or_404(Education, id=edu_id, profile=profile)
        edu.delete()
        return JsonResponse({'status': 'success'})
        
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def candidate_dashboard(request):
    if request.user.role != User.Role.CANDIDATE:
        return redirect('home')
        
    from jobs.models import JobPosting
    from resume.models import Resume

    latest_resume = Resume.objects.filter(user=request.user).order_by('-uploaded_at').first()
    recommended_jobs = []

    if latest_resume and latest_resume.parsed_keywords:
        # Standardize keywords from resume
        resume_words = set(w.strip() for w in latest_resume.parsed_keywords.split() if len(w) > 3)
        all_jobs = JobPosting.objects.filter(is_active=True).select_related('company')
        
        job_scores = []
        for job in all_jobs:
            job_text = f"{job.title} {job.description} {job.requirements}".lower()
            job_words = set(w.strip() for w in job_text.split() if len(w) > 3)
            # Find the intersection count
            match_score = len(resume_words.intersection(job_words))
            if match_score > 3: # Threshold 
                job_scores.append((match_score, job))
                
        # Sort by best match
        job_scores.sort(key=lambda x: x[0], reverse=True)
        recommended_jobs = [{"score": score, "job": job} for score, job in job_scores[:3]]

    return render(request, 'candidate_dashboard.html', {'recommended_jobs': recommended_jobs})

from .models import Connection, ProfileView
from django.db.models import Q

@login_required
def network_dashboard(request):
    if request.user.role != User.Role.CANDIDATE:
        return redirect('home')

    # Connections
    connections_sent = Connection.objects.filter(sender=request.user, status=Connection.Status.ACCEPTED)
    connections_received = Connection.objects.filter(receiver=request.user, status=Connection.Status.ACCEPTED)
    
    established_connections = []
    for c in connections_sent:
        established_connections.append(c.receiver)
    for c in connections_received:
        established_connections.append(c.sender)
        
    incoming_requests = Connection.objects.filter(receiver=request.user, status=Connection.Status.PENDING).select_related('sender')
    
    # Profile Views
    profile_views = []
    has_opted_out = False
    opted_out_count = 0
    
    try:
        if request.user.candidate_profile.opt_out_view_tracking:
            has_opted_out = True
        else:
            raw_views = ProfileView.objects.filter(viewed_user=request.user).order_by('-timestamp')
            # Deduplicate by viewer
            seen_viewers = set()
            for pv in raw_views:
                if pv.viewer not in seen_viewers:
                    # check if the viewer has opted out
                    if hasattr(pv.viewer, 'candidate_profile') and pv.viewer.candidate_profile.opt_out_view_tracking:
                        opted_out_count += 1
                    else:
                        profile_views.append(pv)
                    seen_viewers.add(pv.viewer)
    except CandidateProfile.DoesNotExist:
        pass
        
    return render(request, 'accounts/network.html', {
        'connections': established_connections,
        'incoming_requests': incoming_requests,
        'profile_views': profile_views[:10], # recent 10
        'has_opted_out': has_opted_out,
        'opted_out_count': opted_out_count
    })

@login_required
def candidate_public_profile(request, profile_id):
    target_user = get_object_or_404(User, id=profile_id, role=User.Role.CANDIDATE)
    
    try:
        profile = target_user.candidate_profile
    except CandidateProfile.DoesNotExist:
        messages.warning(request, "This user has not set up their profile yet.")
        return redirect('home')
        
    # Log profile view
    if request.user != target_user:
        # Check if viewer has opted out, if so do we log it? Yes, but we hide their identity later.
        ProfileView.objects.create(viewer=request.user, viewed_user=target_user)
        
    # Determine connection status
    is_connected = False
    connection_status = None
    if request.user.is_authenticated:
        conn = Connection.objects.filter(
            (Q(sender=request.user) & Q(receiver=target_user)) | 
            (Q(sender=target_user) & Q(receiver=request.user))
        ).first()
        if conn:
            connection_status = conn.status
            if conn.status == Connection.Status.ACCEPTED:
                is_connected = True

    # Assess Privacy Filters
    def is_visible(privacy_level):
        if privacy_level == CandidateProfile.PrivacyLevel.PUBLIC:
            return True
        if privacy_level == CandidateProfile.PrivacyLevel.CONNECTIONS and is_connected:
            return True
        if privacy_level == CandidateProfile.PrivacyLevel.PRIVATE and request.user == target_user:
            return True
        if request.user.role == User.Role.EMPLOYER: 
            return True # Employers can see "connections-only" elements inherently if they seek profiles
        return False
        
    context = {
        'target_user': target_user,
        'profile': profile,
        'connection_status': connection_status,
        'is_connected': is_connected,
        
        'show_profile_details': is_visible(profile.visibility),
    }
    
    return render(request, 'accounts/candidate_public_profile.html', context)

@login_required
def send_connection_request(request, to_user_id):
    target_user = get_object_or_404(User, id=to_user_id)
    if request.user == target_user:
        return redirect('candidate_public_profile', profile_id=to_user_id)
        
    Connection.objects.get_or_create(sender=request.user, receiver=target_user)
    messages.success(request, "Connection request sent.")
    return redirect('candidate_public_profile', profile_id=to_user_id)

@login_required
def manage_connection_request(request, req_id, action):
    conn = get_object_or_404(Connection, id=req_id, receiver=request.user)
    if action == 'accept':
        conn.status = Connection.Status.ACCEPTED
        conn.save()
        messages.success(request, f"You are now connected with {conn.sender.first_name}!")
    elif action == 'reject':
        conn.delete()
        messages.info(request, "Connection request declined.")
        
    return redirect('network_dashboard')

@login_required
def remove_connection(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    Connection.objects.filter(
        (Q(sender=request.user) & Q(receiver=target_user)) | 
        (Q(sender=target_user) & Q(receiver=request.user))
    ).delete()
    messages.success(request, "Connection removed.")
    return redirect('network_dashboard')

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

    ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    cache_key = f'bf_lock_admin_{ip}'
    attempts = cache.get(cache_key, 0)
    
    if attempts >= 5:
        form = LoginForm()
        form.add_error(None, 'SECURITY LOCK: IP blocked for 15 minutes due to brute force.')
        return render(request, 'admin/admin_login.html', {'form': form})

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            if user is not None and user.role == User.Role.ADMIN:
                cache.delete(cache_key)
                request.session['pki_passphrase'] = password
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
                attempts += 1
                cache.set(cache_key, attempts, timeout=900)
                if attempts == 5:
                    SecurityAuditLog.objects.create(action_type="BRUTE_FORCE_LOCKOUT", ip_address=ip, details="5 failed ADMIN attempts.")
                    form.add_error(None, 'SECURITY LOCK: IP blocked for 15 minutes due to brute force.')
                else:
                    form.add_error(None, f'Invalid admin credentials. Attempt {attempts}/5.')
    else:
        form = LoginForm()

    return render(request, 'admin/admin_login.html', {'form': form})

@admin_required
def admin_dashboard(request):
    from .models import SecurityAuditLog
    users = User.objects.all().order_by('-date_joined')
    audit_logs = SecurityAuditLog.objects.all().order_by('-timestamp')[:50]
    
    # Perform blockchain integrity check
    for log in audit_logs:
        if log.current_hash:
            log.is_tampered = log.current_hash != log.calculate_hash()
        else:
            log.is_tampered = False
            
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
