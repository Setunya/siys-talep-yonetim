from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Talep, Bildirim 
from .forms import TalepForm, YorumForm
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
            Bildirim.objects.create(
                kullanici=talep.atanan,
                mesaj=f"Size yeni bir talep atandı: {talep.baslik}",
                talep=talep
            )
            return redirect('talep_listesi')
    else:
        form = TalepForm()

    return render(request, 'gorevler/talep_form.html', {'form': form})
@login_required
def talep_detay(request, talep_id):
    talep = Talep.objects.get(id=talep_id, silindi_mi=False)

    if not takim_lideri_mi(request.user) and talep.atanan != request.user:
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        form = YorumForm(request.POST)
        if form.is_valid():
            yorum = form.save(commit=False)
            yorum.talep = talep
            yorum.yazan = request.user
            yorum.save()
            if talep.atanan != request.user:
                alici = talep.atanan
            else:
                alici = talep.olusturan
            Bildirim.objects.create(
                kullanici=alici,
                mesaj=f"Talebinize yorum eklendi: {talep.baslik}",
                talep=talep
            )
            return redirect('talep_detay', talep_id=talep.id)
    else:
        form = YorumForm()

    return render(request, 'gorevler/talep_detay.html', {
        'talep': talep,
        'form': form,
    })


@login_required
def bildirimler(request):
    liste = request.user.bildirimler.all()
    request.user.bildirimler.filter(okundu=False).update(okundu=True)
    return render(request, 'gorevler/bildirimler.html', {'liste': liste})