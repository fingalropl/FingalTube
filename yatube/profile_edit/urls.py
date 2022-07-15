from django.urls import path

from . import views

app_name = 'profile_edit'

urlpatterns = [
    path('profile_edit/<str:username>/', views.profile_edit, name='profile_edit'),
]
