from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('<int:thread_id>/', views.thread_detail_view, name='thread_detail'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('group/new/', views.create_group_chat, name='create_group_chat'),
]
