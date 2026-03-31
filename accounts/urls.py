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
    path('dashboard/employer/', views.employer_dashboard, name='employer_dashboard'),
    
    # Admin Stealth URLs
    path('secure-hq/login/', views.admin_login, name='admin_login'),
    path('secure-hq/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('secure-hq/moderate/<int:user_id>/<str:action>/', views.moderate_user, name='moderate_user'),
]
