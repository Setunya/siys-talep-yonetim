from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Talep, Bildirim
from .forms import TalepForm, YorumForm
from hesaplar.yetkiler import takim_lideri_mi
from .loglama import log_yaz


@login_required
def talep_listesi(request):
    talepler = Talep.objects.filter(silindi_mi=False).select_related(
        'birim', 'modul', 'talep_turu', 'atanan'
    )

    # Yatay yetki: personel yalnızca kendi taleplerini görür (değiştirilmedi).
    if not takim_lideri_mi(request.user):
        talepler = talepler.filter(atanan=request.user)

    # Arama ve filtreleme — yalnızca yetki dâhilindeki küme üzerinde çalışır,
    # dolayısıyla filtre parametresiyle yetki sınırı aşılamaz.
    arama = request.GET.get('arama', '').strip()
    durum = request.GET.get('durum', '').strip()
    oncelik = request.GET.get('oncelik', '').strip()

    if arama:
        talepler = talepler.filter(
            Q(baslik__icontains=arama) | Q(birim__ad__icontains=arama)
        )
    if durum in Talep.Durum.values:
        talepler = talepler.filter(durum=durum)
    if oncelik in Talep.Oncelik.values:
        talepler = talepler.filter(oncelik=oncelik)

    # Sayfalama: sayfa başına 10 kayıt.
    sayfalayici = Paginator(talepler, 10)
    sayfa = sayfalayici.get_page(request.GET.get('sayfa'))

    return render(request, 'gorevler/talep_listesi.html', {
        'talepler': sayfa,          # Page nesnesi de döngüde gezilebilir
        'sayfa_obj': sayfa,
        'takim_lideri': takim_lideri_mi(request.user),
        'arama': arama,
        'secili_durum': durum,
        'secili_oncelik': oncelik,
        'durumlar': Talep.Durum.choices,
        'oncelikler': Talep.Oncelik.choices,
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
            log_yaz(request, f"Talep olusturuldu: {talep.baslik}")
            return redirect('talep_listesi')
    else:
        form = TalepForm()

    return render(request, 'gorevler/talep_form.html', {'form': form})


@login_required
def talep_detay(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)

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
            log_yaz(request, f"Yorum eklendi: {talep.baslik}")
            return redirect('talep_detay', talep_id=talep.id)
    else:
        form = YorumForm()

    return render(request, 'gorevler/talep_detay.html', {
        'talep': talep,
        'form': form,
        'takim_lideri': takim_lideri_mi(request.user),
    })


@login_required
def bildirimler(request):
    liste = request.user.bildirimler.all()
    request.user.bildirimler.filter(okundu=False).update(okundu=True)
    return render(request, 'gorevler/bildirimler.html', {'liste': liste})


@login_required
def durum_degistir(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)

    # Yetki: takım lideri veya bu talebin sahibi
    if not takim_lideri_mi(request.user) and talep.atanan != request.user:
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        yeni_durum = request.POST.get('durum')

        # İzinli geçişler
        izinli = {
            'BEKLIYOR': ['ANALIZDE'],
            'ANALIZDE': ['GELISTIRILIYOR'],
            'GELISTIRILIYOR': ['TESTTE'],
            'TESTTE': ['TAMAMLANDI', 'GELISTIRILIYOR'],
            'TAMAMLANDI': [],
        }

        if yeni_durum not in izinli.get(talep.durum, []):
            return redirect('talep_detay', talep_id=talep.id)

        # Tamamlandı'ya sadece takım lideri geçirebilir
        if yeni_durum == 'TAMAMLANDI' and not takim_lideri_mi(request.user):
            return redirect('talep_detay', talep_id=talep.id)

        talep.durum = yeni_durum
        talep.save()
        log_yaz(request, f"Durum degistirildi: {talep.baslik} -> {yeni_durum}")

    return redirect('talep_detay', talep_id=talep.id)

@login_required
def denetim_kayitlari(request):
    if not takim_lideri_mi(request.user):
        return render(request, 'gorevler/yetkisiz.html')

    from .models import DenetimKaydi
    kayitlar = DenetimKaydi.objects.all()[:200]
    return render(request, 'gorevler/denetim.html', {'kayitlar': kayitlar})

from django.utils import timezone


@login_required
def talep_sil(request, talep_id):
    if not takim_lideri_mi(request.user):
        return render(request, 'gorevler/yetkisiz.html')

    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)

    if request.method == 'POST':
        talep.silindi_mi = True
        talep.silme_tarihi = timezone.now()
        talep.silen = request.user
        talep.save()
        log_yaz(request, f"Talep arsivlendi: {talep.baslik}")
        return redirect('talep_listesi')

    return render(request, 'gorevler/talep_sil.html', {'talep': talep})

@login_required
def kanban(request):
    talepler = Talep.objects.filter(silindi_mi=False)

    if not takim_lideri_mi(request.user):
        talepler = talepler.filter(atanan=request.user)

    return render(request, 'gorevler/kanban.html', {
        'bekliyor': talepler.filter(durum='BEKLIYOR'),
        'analizde': talepler.filter(durum='ANALIZDE'),
        'gelistiriliyor': talepler.filter(durum='GELISTIRILIYOR'),
        'testte': talepler.filter(durum='TESTTE'),
        'tamamlandi': talepler.filter(durum='TAMAMLANDI'),
    })

@login_required
def dashboard(request):
    talepler = Talep.objects.filter(silindi_mi=False)

    if not takim_lideri_mi(request.user):
        talepler = talepler.filter(atanan=request.user)

    bugun = timezone.now().date()

    return render(request, 'gorevler/dashboard.html', {
        'toplam': talepler.count(),
        'acik': talepler.exclude(durum='TAMAMLANDI').count(),
        'tamamlanan': talepler.filter(durum='TAMAMLANDI').count(),
        'gecikmis': talepler.exclude(durum='TAMAMLANDI').filter(hedef_tarih__lt=bugun).count(),
        'yaklasanlar': talepler.exclude(durum='TAMAMLANDI').filter(
            hedef_tarih__gte=bugun
        ).order_by('hedef_tarih')[:5],
    })