from django.db import models
from django.conf import settings

class Company(models.Model):
    employer = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=255)
    description = models.TextField()
    website = models.URLField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class JobPosting(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FT', 'Full Time'
        PART_TIME = 'PT', 'Part Time'
        CONTRACT = 'CT', 'Contract'
        INTERNSHIP = 'IN', 'Internship'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='job_postings')
    title = models.CharField(max_length=255)
    description = models.TextField()
    requirements = models.TextField(blank=True)
    location = models.CharField(max_length=255)
    
    employment_type = models.CharField(max_length=2, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME)
    salary_range = models.CharField(max_length=100, blank=True, help_text="e.g. $80,000 - $120,000")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    cryptographic_signature = models.TextField(blank=True, help_text="RSA PKCS#1v1.5 signature of job data")

    def __str__(self):
        return f"{self.title} at {self.company.name}"

class Application(models.Model):
    class ApplicationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Review'
        IN_REVIEW = 'REVIEW', 'In Review'
        ACCEPTED = 'ACCEPTED', 'Accepted / Offer'
        REJECTED = 'REJECTED', 'Rejected'

    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    resume = models.ForeignKey('resume.Resume', on_delete=models.SET_NULL, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.PENDING)
    cover_letter = models.TextField(blank=True)
    
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('job', 'candidate')

    def __str__(self):
        return f"{self.candidate.email} -> {self.job.title}"
