from django.shortcuts import render

from .models import Talep #models.py d en talep tablosunu getiriyoruz

def talep_listesi(request):
    talepler = Talep.objects.filter(silindi_mi=False)
    #veritabanından arşivlenmemiş talepleri çekip talepler kutusuna koyuyoruz. 
    #.objects: Tabloya eriş, .filter(): şu şartı sağlayanları getir.
    return render(request, 'gorevler/talep_listesi.html', {'talepler': talepler})
#şu şablonu al, içine şu veriyi koy, sayfayı üret.