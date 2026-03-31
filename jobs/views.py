from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import User
from .models import Company, JobPosting
from .forms import CompanyForm, JobPostingForm

# --- EMPLOYER VIEWS ---

@login_required
def company_setup(request):
    """ Allows an Employer to create or update their Company profile. """
    if request.user.role != User.Role.EMPLOYER:
        messages.error(request, "Only employers can create unstop profiles.")
        return redirect('home')
        
    company, created = Company.objects.get_or_create(employer=request.user)
    
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, "Company profile updated successfully!")
            return redirect('employer_dashboard')
    else:
        form = CompanyForm(instance=company)
        
    return render(request, 'jobs/company_setup.html', {'form': form, 'company': company})

@login_required
def job_create(request):
    """ Allows an Employer to post a new job under their Company. """
    if request.user.role != User.Role.EMPLOYER:
        return redirect('home')
        
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.warning(request, "You must clear your company profile first.")
        return redirect('company_setup')
        
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            messages.success(request, f"Successfully created job posting: {job.title}")
            return redirect('employer_jobs_list')
    else:
        form = JobPostingForm()
        
    return render(request, 'jobs/job_create.html', {'form': form})

@login_required
def employer_jobs_list(request):
    """ View all jobs created by this employer. """
    if request.user.role != User.Role.EMPLOYER:
        return redirect('home')
        
    try:
        company = request.user.company
        jobs = company.job_postings.all().order_by('-created_at')
    except Company.DoesNotExist:
        company = None
        jobs = []

    return render(request, 'jobs/employer_jobs_list.html', {'jobs': jobs, 'company': company})

@login_required
def employer_job_applications(request, job_id):
    """ View all candidates who applied to a specific job. """
    if request.user.role != User.Role.EMPLOYER:
        return redirect('home')
        
    job = get_object_or_404(JobPosting, pk=job_id, company__employer=request.user)
    applications = job.applications.all().order_by('-applied_at').select_related('candidate', 'resume')
    
    return render(request, 'jobs/employer_job_applications.html', {'job': job, 'applications': applications})

@login_required
def update_application_status(request, app_id, next_status):
    """ Update the status of an application. """
    if request.user.role != User.Role.EMPLOYER:
        return redirect('home')
        
    application = get_object_or_404(Application, pk=app_id, job__company__employer=request.user)
    
    # Simple validation using choices
    valid_statuses = dict(Application.ApplicationStatus.choices).keys()
    if next_status in valid_statuses:
        application.status = next_status
        application.save()
        messages.success(request, f"Updated application status to {dict(Application.ApplicationStatus.choices)[next_status]}.")
    
    return redirect('employer_job_applications', job_id=application.job.id)

# --- CANDIDATE VIEWS ---

@login_required
def job_board(request):
    """ Shows a searchable grid of all active open jobs to Candidates. """
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    
    jobs = JobPosting.objects.filter(is_active=True).select_related('company')
    
    if query:
        jobs = jobs.filter(title__icontains=query) | jobs.filter(company__name__icontains=query)
    if location:
        jobs = jobs.filter(location__icontains=location)
        
    jobs = jobs.order_by('-created_at')
    
    return render(request, 'jobs/job_board.html', {'jobs': jobs, 'query': query, 'location': location})

@login_required
def job_detail(request, pk):
    """ Displays details for a single job posting. """
    job = get_object_or_404(JobPosting, pk=pk)
    
    # Check if the current user has already applied
    has_applied = False
    if request.user.is_authenticated and request.user.role == User.Role.CANDIDATE:
        has_applied = Application.objects.filter(job=job, candidate=request.user).exists()
        
    return render(request, 'jobs/job_detail.html', {'job': job, 'has_applied': has_applied})

@login_required
def company_public_detail(request, pk):
    """ Public profile page for a company. """
    company = get_object_or_404(Company, pk=pk)
    active_jobs = company.job_postings.filter(is_active=True)
    return render(request, 'jobs/company_public_detail.html', {'company': company, 'jobs': active_jobs})

from .models import Application
from .forms import ApplicationForm

@login_required
def apply_for_job(request, job_id):
    """ Handles the candidate applying to a job with their resume. """
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only candidates can apply to jobs.")
        return redirect('job_board')
        
    job = get_object_or_404(JobPosting, pk=job_id)
    
    if Application.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, "You have already applied for this role.")
        return redirect('job_detail', pk=job_id)
        
    if request.method == 'POST':
        form = ApplicationForm(request.POST, candidate=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()
            messages.success(request, f"Successfully applied for {job.title}!")
            return redirect('candidate_applications')
    else:
        form = ApplicationForm(candidate=request.user)
        
    return render(request, 'jobs/apply.html', {'form': form, 'job': job})

@login_required
def candidate_applications(request):
    """ View all applications submitted by the candidate. """
    if request.user.role != User.Role.CANDIDATE:
        return redirect('home')
        
    applications = Application.objects.filter(candidate=request.user).order_by('-applied_at').select_related('job', 'job__company')
    return render(request, 'jobs/candidate_applications.html', {'applications': applications})
