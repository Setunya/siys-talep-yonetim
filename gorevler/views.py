from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Talep
from .forms import TalepForm
from hesaplar.yetkiler import takim_lideri_mi


@login_required
def talep_listesi(request):
    talepler = Talep.objects.filter(silindi_mi=False)

    if not takim_lideri_mi(request.user):
        talepler = talepler.filter(atanan=request.user)

    return render(request, 'gorevler/talep_listesi.html', {
        'talepler': talepler,
        'takim_lideri': takim_lideri_mi(request.user),
    })


@login_required
def talep_olustur(request):
    if not takim_lideri_mi(request.user):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        form = TalepForm(request.POST)
        if form.is_valid():
            talep = form.save(commit=False)
            talep.olusturan = request.user
            talep.save()
            return redirect('talep_listesi')
    else:
        form = TalepForm()

    return render(request, 'gorevler/talep_form.html', {'form': form})

@login_required
def talep_detay(request, talep_id):
    talep = Talep.objects.get(id=talep_id, silindi_mi=False)

    if not takim_lideri_mi(request.user) and talep.atanan != request.user:
        return render(request, 'gorevler/yetkisiz.html')

    return render(request, 'gorevler/talep_detay.html', {'talep': talep})