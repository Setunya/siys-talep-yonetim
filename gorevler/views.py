from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Talep
from hesaplar.yetkiler import takim_lideri_mi


@login_required
def talep_listesi(request):
    talepler = Talep.objects.filter(silindi_mi=False)

    if not takim_lideri_mi(request.user):
        talepler = talepler.filter(atanan=request.user)

    return render(request, 'gorevler/talep_listesi.html', {'talepler': talepler})