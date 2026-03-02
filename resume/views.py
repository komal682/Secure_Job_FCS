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
