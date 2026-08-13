from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='anasayfa'),
    path('talepler/', views.talep_listesi, name='talep_listesi'),
    path('talepler/yeni/', views.talep_olustur, name='talep_olustur'),
    path('talepler/<int:talep_id>/', views.talep_detay, name='talep_detay'),
    path('talepler/<int:talep_id>/durum/', views.durum_degistir, name='durum_degistir'),
    path('talepler/<int:talep_id>/ata/', views.talep_ata, name='talep_ata'),
    path('talepler/<int:talep_id>/reddet/', views.talep_reddet, name='talep_reddet'),
    path('talepler/<int:talep_id>/sil/', views.talep_sil, name='talep_sil'),
    path('gelen-talepler/', views.gelen_talepler, name='gelen_talepler'),
    path('reddedilenler/', views.reddedilenler, name='reddedilenler'),
    path('kanban/', views.kanban, name='kanban'),
    path('bildirimler/', views.bildirimler, name='bildirimler'),
    path('denetim/', views.denetim_kayitlari, name='denetim_kayitlari'),
]