from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('role-selection/<str:action>/', views.role_selection, name='role_selection'),
    path('register/<str:role>/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('totp/setup/', views.totp_setup, name='totp_setup'),
    path('totp/verify/', views.totp_verify, name='totp_verify'),
    path('dashboard/candidate/', views.candidate_dashboard, name='candidate_dashboard'),
    # React Profile Modular API Routes
    path('api/profile/', views.api_get_profile, name='api_get_profile'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
    path('api/profile/education/', views.api_education, name='api_add_education'),
    path('api/profile/education/<int:edu_id>/', views.api_education, name='api_modify_education'),
    
    path('dashboard/employer/', views.employer_dashboard, name='employer_dashboard'),
    
    # Professional Networking (Section A)
    path('network/', views.network_dashboard, name='network_dashboard'),
    path('candidate/<int:profile_id>/', views.candidate_public_profile, name='candidate_public_profile'),
    path('network/connect/<int:to_user_id>/', views.send_connection_request, name='send_connection_request'),
    path('network/manage/<int:req_id>/<str:action>/', views.manage_connection_request, name='manage_connection_request'),
    path('network/remove/<int:user_id>/', views.remove_connection, name='remove_connection'),
    
    # Admin Stealth URLs
    path('secure-hq/login/', views.admin_login, name='admin_login'),
    path('secure-hq/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('secure-hq/moderate/<int:user_id>/<str:action>/', views.moderate_user, name='moderate_user'),
]
