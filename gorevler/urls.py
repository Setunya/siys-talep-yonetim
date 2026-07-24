from django.urls import path
from . import views

urlpatterns = [
    path('talepler/', views.talep_listesi, name='talep_listesi'),
]