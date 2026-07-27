from django.urls import path
from . import views

urlpatterns = [
    path('talepler/', views.talep_listesi, name='talep_listesi'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.talep_listesi, name='anasayfa'),
    path('talepler/', views.talep_listesi, name='talep_listesi'),
    path('talepler/yeni/', views.talep_olustur, name='talep_olustur'),
]

urlpatterns = [
    path('', views.talep_listesi, name='anasayfa'),
    path('talepler/', views.talep_listesi, name='talep_listesi'),
    path('talepler/yeni/', views.talep_olustur, name='talep_olustur'),
    path('talepler/<int:talep_id>/', views.talep_detay, name='talep_detay'),
    path('bildirimler/', views.bildirimler, name='bildirimler'),
]