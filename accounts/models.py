from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
import hashlib

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        CANDIDATE = 'CANDIDATE', 'Candidate'
        EMPLOYER = 'EMPLOYER', 'Employer'
    
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)
    
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    is_totp_enabled = models.BooleanField(default=False)
    
    public_key = models.TextField(blank=True)
    private_key_encrypted = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

class SecurityAuditLog(models.Model):
    action_type = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    previous_hash = models.CharField(max_length=64, blank=True)
    current_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def calculate_hash(self):
        base_string = f"{self.action_type}{self.user_id}{self.ip_address}{self.details}{self.previous_hash}"
        return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        is_new_block = False
        if not self.pk and not self.previous_hash:
            is_new_block = True
            last_log = SecurityAuditLog.objects.order_by('-id').first()
            self.previous_hash = last_log.current_hash if last_log and last_log.current_hash else "0" * 64
            self.current_hash = self.calculate_hash()
            
        super().save(*args, **kwargs)
        
        # Zero-Cost WORM Emulation
        if is_new_block:
            try:
                import json
                import os
                log_data = json.dumps({
                    "id": self.id,
                    "action_type": self.action_type,
                    "user_id": self.user_id,
                    "ip_address": self.ip_address,
                    "details": self.details,
                    "timestamp": self.timestamp.isoformat() if self.timestamp else "",
                    "previous_hash": self.previous_hash,
                    "current_hash": self.current_hash
                }) + "\n"
                worm_file_path = os.path.join(settings.BASE_DIR, 'security_audit_worm.log')
                with open(worm_file_path, 'a') as f:
                    f.write(log_data)
            except Exception as e:
                # Silently catch so we don't break the application if IO fails
                pass

    def __str__(self):
        return f"{self.action_type} - {self.user} - {self.timestamp}"

class CandidateProfile(models.Model):
    class PrivacyLevel(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        CONNECTIONS = 'CONNECTIONS', 'Connections Only'
        PRIVATE = 'PRIVATE', 'Private'

    candidate = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='candidate_profile')
    photo = models.ImageField(upload_to='candidate_photos/', blank=True, null=True)
    
    summary = models.TextField(blank=True, help_text="Short professional bio or objective.")
    skills = models.TextField(blank=True, help_text="Comma-separated list of skills.")
    
    visibility = models.CharField(max_length=15, choices=PrivacyLevel.choices, default=PrivacyLevel.PUBLIC, help_text="Who can see your profile details?")
    
    opt_out_view_tracking = models.BooleanField(default=False, help_text="Do not track who viewed your profile, and do not let others see you viewed theirs.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.candidate.email}"

class Connection(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_connections', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_connections', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('sender', 'receiver')

    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email} ({self.status})"

class ProfileView(models.Model):
    viewer = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='profiles_viewed', on_delete=models.CASCADE)
    viewed_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='profile_views_received', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.viewer.email} viewed {self.viewed_user.email}"

class Education(models.Model):
    profile = models.ForeignKey(CandidateProfile, related_name='educations', on_delete=models.CASCADE)
    school = models.CharField(max_length=255)
    degree = models.CharField(max_length=255, blank=True)
    field_of_study = models.CharField(max_length=255, blank=True)
    
    start_month = models.CharField(max_length=20, blank=True)
    start_year = models.CharField(max_length=4, blank=True)
    end_month = models.CharField(max_length=20, blank=True)
    end_year = models.CharField(max_length=4, blank=True)
    
    grade = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-end_year', '-start_year']

    def __str__(self):
        return f"{self.degree} at {self.school}"
