from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_resume, name='upload_resume'),
    path('success/', views.upload_success, name='upload_success'),
    path('list/', views.resume_list, name='resume_list'),
    path('download/<int:resume_id>/', views.download_decrypted_resume, name='download_decrypted_resume'),
]
