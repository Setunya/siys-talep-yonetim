from django.contrib import admin
from .models import Birim, TalepTuru, Modul, Talep


# Birim tablosunu panele ekle
@admin.register(Birim)
class BirimAdmin(admin.ModelAdmin):
    list_display = ['ad', 'aktif']       # Listede görünecek sütunlar
    list_filter = ['aktif']              # Sağdaki filtre kutusu
    search_fields = ['ad']               # Arama kutusu


@admin.register(TalepTuru)
class TalepTuruAdmin(admin.ModelAdmin):
    list_display = ['ad', 'aktif']
    list_filter = ['aktif']


@admin.register(Modul)
class ModulAdmin(admin.ModelAdmin):
    list_display = ['ad', 'aktif']
    list_filter = ['aktif']


@admin.register(Talep)
class TalepAdmin(admin.ModelAdmin):
    # Talep listesinde görünecek sütunlar
    list_display = ['baslik', 'birim', 'modul', 'talep_turu',
                    'atanan', 'durum', 'oncelik', 'hedef_tarih']
    # Sağ taraftaki filtreler
    list_filter = ['durum', 'oncelik', 'talep_turu', 'modul', 'silindi_mi']
    # Arama kutusu — başlık ve birim adından arama
    search_fields = ['baslik', 'birim__ad']
    # Üstte tarih gezinme çubuğu
    date_hierarchy = 'olusturma_tarihi'