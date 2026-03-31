from django.urls import path
from . import views

urlpatterns = [
    # Candidate Job Board & Applications
    path('board/', views.job_board, name='job_board'),
    path('job/<int:pk>/', views.job_detail, name='job_detail'),
    path('company/<int:pk>/', views.company_public_detail, name='company_public_detail'),
    path('apply/<int:job_id>/', views.apply_for_job, name='apply_for_job'),
    path('candidate/applications/', views.candidate_applications, name='candidate_applications'),
    
    # Employer Dashboard Setup
    path('employer/company/setup/', views.company_setup, name='company_setup'),
    path('employer/job/create/', views.job_create, name='job_create'),
    path('employer/jobs/', views.employer_jobs_list, name='employer_jobs_list'),
    path('employer/jobs/<int:job_id>/applications/', views.employer_job_applications, name='employer_job_applications'),
    path('employer/applications/<int:app_id>/status/<str:next_status>/', views.update_application_status, name='update_application_status'),
]
