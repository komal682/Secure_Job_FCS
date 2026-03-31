from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.conf import settings
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
from .models import Resume
from .forms import ResumeUploadForm
from django.contrib.auth.decorators import login_required

@login_required
def upload_resume(request):
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['resume_file']
            file_data = file.read()
            
            # AES-256 encryption
            key = settings.RESUME_ENCRYPTION_KEY
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_data = iv + encryptor.update(file_data) + encryptor.finalize()
            
            # Save to database mapped to current user
            Resume.objects.create(
                user=request.user,
                encrypted_file=encrypted_data,
                original_filename=file.name
            )
            return redirect('upload_success')
    else:
        form = ResumeUploadForm()
    return render(request, 'resume/upload.html', {'form': form})

@login_required
def upload_success(request):
    return render(request, 'resume/success.html')

@login_required
def resume_list(request):
    from accounts.models import User
    if request.user.role == User.Role.CANDIDATE:
        resumes = Resume.objects.filter(user=request.user)
    else:
        resumes = Resume.objects.all()
    return render(request, 'resume/list.html', {'resumes': resumes})

from django.http import HttpResponse, Http404

@login_required
def download_decrypted_resume(request, resume_id):
    resume = Resume.objects.get(id=resume_id)
    
    # Access Control Mapping
    from accounts.models import User
    from jobs.models import Application
    if request.user.role == User.Role.CANDIDATE and resume.user != request.user:
        raise Http404("Not authorized you are not the owner of this encrypted file.")
        
    if request.user.role == User.Role.EMPLOYER:
        has_access = Application.objects.filter(job__company__employer=request.user, resume=resume).exists()
        if not has_access:
            raise Http404("Not authorized to view this application's vault.")
            
    # Load into memory block
    encrypted_data = bytes(resume.encrypted_file) if isinstance(resume.encrypted_file, memoryview) else resume.encrypted_file
    
    # Parse IV block
    iv = encrypted_data[:16]
    actual_encrypted = encrypted_data[16:]
    
    # Decrypt
    key = settings.RESUME_ENCRYPTION_KEY
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(actual_encrypted) + decryptor.finalize()
    
    # Serve to browser securely from memory
    response = HttpResponse(decrypted_data, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="decrypted_resume.pdf"'
    # We use extension .pdf by default or we can use the original if text
    if resume.original_filename.endswith('.txt'):
        response['Content-Type'] = 'text/plain'
        response['Content-Disposition'] = f'inline; filename="decrypted_{resume.original_filename}"'
    else:
        response['Content-Disposition'] = f'inline; filename="{resume.original_filename}"'
        
    return response
