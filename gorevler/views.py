from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone

from .models import Talep, Bildirim, DenetimKaydi
from .forms import TalepForm, YorumForm
from .loglama import log_yaz
from hesaplar.yetkiler import departman_muduru_mu, talep_eden_mi


# ---------------------------------------------------------------------------
# Rol bazlı kapsam yardımcıları (yatay yetki / IDOR koruması)
# ---------------------------------------------------------------------------

def gorunecek_talepler(user):
    """
    Kullanıcının yetkisi dâhilindeki (arşivlenmemiş) talep kümesi:
    - Müdür  → yönettiği departmanlara gelen talepler
    - Talep Eden → kendi açtığı talepler
    - Personel → kendisine atanan talepler
    """
    qs = Talep.objects.filter(silindi_mi=False).select_related(
        'birim', 'modul', 'talep_turu', 'atanan', 'departman', 'olusturan'
    )
    if user.is_superuser:
        return qs
    if departman_muduru_mu(user):
        return qs.filter(departman__mudur=user)
    if talep_eden_mi(user):
        return qs.filter(olusturan=user)
    return qs.filter(atanan=user)


def talebin_muduru_mu(user, talep):
    """Kullanıcı, bu talebin ait olduğu departmanın müdürü mü?"""
    if user.is_superuser:
        return True
    return (
        departman_muduru_mu(user)
        and talep.departman_id is not None
        and talep.departman.mudur_id == user.id
    )


def talebi_gorebilir_mi(user, talep):
    """Yatay yetki: talebi görüntüleme hakkı var mı?"""
    return (
        talebin_muduru_mu(user, talep)
        or talep.atanan_id == user.id
        or talep.olusturan_id == user.id
    )


def personel_listesi():
    """Atama için seçilebilecek personeller."""
    return User.objects.filter(
        groups__name='Personel', is_active=True
    ).order_by('first_name', 'username')


# ---------------------------------------------------------------------------
# Talep listesi
# ---------------------------------------------------------------------------

@login_required
def talep_listesi(request):
    # Reddedilenler ayrı sekmede gösterilir; ana listede yer almaz.
    talepler = gorunecek_talepler(request.user).exclude(durum='REDDEDILDI')

    arama = request.GET.get('arama', '').strip()
    durum = request.GET.get('durum', '').strip()
    oncelik = request.GET.get('oncelik', '').strip()

    if arama:
        talepler = talepler.filter(
            Q(baslik__icontains=arama) | Q(birim__ad__icontains=arama)
        )
    if durum in Talep.Durum.values and durum != 'REDDEDILDI':
        talepler = talepler.filter(durum=durum)
    if oncelik in Talep.Oncelik.values:
        talepler = talepler.filter(oncelik=oncelik)

    sayfalayici = Paginator(talepler, 10)
    sayfa = sayfalayici.get_page(request.GET.get('sayfa'))

    # Durum filtresi seçenekleri (Reddedildi hariç).
    durum_secenekleri = [
        (d, e) for d, e in Talep.Durum.choices if d != 'REDDEDILDI'
    ]

    return render(request, 'gorevler/talep_listesi.html', {
        'talepler': sayfa,
        'sayfa_obj': sayfa,
        'arama': arama,
        'secili_durum': durum,
        'secili_oncelik': oncelik,
        'durumlar': durum_secenekleri,
        'oncelikler': Talep.Oncelik.choices,
    })


# ---------------------------------------------------------------------------
# Talep oluşturma (Talep Eden rolü) — atama YAPILMAZ, departmana yönlendirilir
# ---------------------------------------------------------------------------

@login_required
def talep_olustur(request):
    if not talep_eden_mi(request.user):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        form = TalepForm(request.POST)
        if form.is_valid():
            talep = form.save(commit=False)
            talep.olusturan = request.user
            talep.atanan = None          # önce atanmamış gelir
            talep.durum = Talep.Durum.BEKLIYOR
            # Departman, seçilen modüle (konuya) göre otomatik belirlenir.
            talep.departman = talep.modul.departman
            talep.save()

            # Sistem talebi otomatik ilgili departman müdürüne yönlendirir.
            mudur = talep.departman.mudur if talep.departman_id else None
            if mudur:
                Bildirim.objects.create(
                    kullanici=mudur,
                    mesaj=f"Departmanınıza yeni talep geldi: {talep.baslik}",
                    talep=talep,
                )
            log_yaz(request, f"Talep olusturuldu: {talep.baslik}")
            return redirect('talep_listesi')
    else:
        form = TalepForm()

    return render(request, 'gorevler/talep_form.html', {'form': form})


# ---------------------------------------------------------------------------
# Talep detay + yorum
# ---------------------------------------------------------------------------

@login_required
def talep_detay(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)

    if not talebi_gorebilir_mi(request.user, talep):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        form = YorumForm(request.POST)
        if form.is_valid():
            yorum = form.save(commit=False)
            yorum.talep = talep
            yorum.yazan = request.user
            yorum.save()
            if talep.atanan and talep.atanan != request.user:
                alici = talep.atanan
            else:
                alici = talep.olusturan
            if alici and alici != request.user:
                Bildirim.objects.create(
                    kullanici=alici,
                    mesaj=f"Talebinize yorum eklendi: {talep.baslik}",
                    talep=talep,
                )
            log_yaz(request, f"Yorum eklendi: {talep.baslik}")
            return redirect('talep_detay', talep_id=talep.id)
    else:
        form = YorumForm()

    bu_talebin_muduru = talebin_muduru_mu(request.user, talep)

    return render(request, 'gorevler/talep_detay.html', {
        'talep': talep,
        'form': form,
        'bu_talebin_muduru': bu_talebin_muduru,
        # Müdür, atanmamış talebi personele atayabilir.
        'personeller': personel_listesi() if bu_talebin_muduru else None,
    })


# ---------------------------------------------------------------------------
# Müdür: gelen talepleri personele atama
# ---------------------------------------------------------------------------

@login_required
def talep_ata(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)
    if not talebin_muduru_mu(request.user, talep):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        personel = User.objects.filter(
            id=request.POST.get('atanan'), is_active=True
        ).first()
        if personel:
            talep.atanan = personel
            talep.save()
            Bildirim.objects.create(
                kullanici=personel,
                mesaj=f"Size yeni bir talep atandı: {talep.baslik}",
                talep=talep,
            )
            log_yaz(request, f"Talep atandi: {talep.baslik} -> {personel.username}")

    return redirect('talep_detay', talep_id=talep.id)


# ---------------------------------------------------------------------------
# Müdür: talebi gerekçeyle reddetme
# ---------------------------------------------------------------------------

@login_required
def talep_reddet(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)
    if not talebin_muduru_mu(request.user, talep):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        gerekce = request.POST.get('red_gerekce', '').strip()
        if not gerekce:
            # Gerekçe zorunlu; boşsa reddetme işlemi yapılmaz.
            return redirect('talep_detay', talep_id=talep.id)
        talep.durum = Talep.Durum.REDDEDILDI
        talep.red_gerekce = gerekce
        talep.red_eden = request.user
        talep.red_tarihi = timezone.now()
        talep.save()
        Bildirim.objects.create(
            kullanici=talep.olusturan,
            mesaj=f"Talebiniz reddedildi: {talep.baslik}",
            talep=talep,
        )
        log_yaz(request, f"Talep reddedildi: {talep.baslik}")

    return redirect('talep_detay', talep_id=talep.id)


# ---------------------------------------------------------------------------
# Müdür: gelen (atanmamış) talepler kutusu
# ---------------------------------------------------------------------------

@login_required
def gelen_talepler(request):
    if not departman_muduru_mu(request.user):
        return render(request, 'gorevler/yetkisiz.html')

    talepler = gorunecek_talepler(request.user).filter(
        atanan__isnull=True, durum='BEKLIYOR'
    ).order_by('hedef_tarih')

    return render(request, 'gorevler/gelen_talepler.html', {'talepler': talepler})


# ---------------------------------------------------------------------------
# Reddedilen talepler sekmesi
# ---------------------------------------------------------------------------

@login_required
def reddedilenler(request):
    talepler = gorunecek_talepler(request.user).filter(
        durum='REDDEDILDI'
    ).select_related('red_eden').order_by('-red_tarihi')
    return render(request, 'gorevler/reddedilenler.html', {'talepler': talepler})


# ---------------------------------------------------------------------------
# Bildirimler
# ---------------------------------------------------------------------------

@login_required
def bildirimler(request):
    liste = request.user.bildirimler.all()
    request.user.bildirimler.filter(okundu=False).update(okundu=True)
    return render(request, 'gorevler/bildirimler.html', {'liste': liste})


# ---------------------------------------------------------------------------
# Durum değiştirme (kurallı geçişler)
# ---------------------------------------------------------------------------

@login_required
def durum_degistir(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)

    # Yetki: bu talebin müdürü veya atanan personeli.
    if not (talebin_muduru_mu(request.user, talep) or talep.atanan_id == request.user.id):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        # Atanmamış talep süreçte ilerletilemez (önce atanmalı).
        if talep.atanan_id is None:
            return redirect('talep_detay', talep_id=talep.id)

        yeni_durum = request.POST.get('durum')

        # İzinli geçişler (durum makinesi).
        izinli = {
            'BEKLIYOR': ['ANALIZDE'],
            'ANALIZDE': ['GELISTIRILIYOR'],
            'GELISTIRILIYOR': ['TESTTE'],
            'TESTTE': ['TAMAMLANDI', 'GELISTIRILIYOR'],
            'TAMAMLANDI': [],
        }

        if yeni_durum not in izinli.get(talep.durum, []):
            return redirect('talep_detay', talep_id=talep.id)

        # Tamamlandı'ya yalnızca departman müdürü geçirebilir (onay).
        if yeni_durum == 'TAMAMLANDI' and not talebin_muduru_mu(request.user, talep):
            return redirect('talep_detay', talep_id=talep.id)

        talep.durum = yeni_durum
        talep.save()
        log_yaz(request, f"Durum degistirildi: {talep.baslik} -> {yeni_durum}")

    return redirect('talep_detay', talep_id=talep.id)


# ---------------------------------------------------------------------------
# Denetim kayıtları (müdür) — kullanıcı filtreli
# ---------------------------------------------------------------------------

@login_required
def denetim_kayitlari(request):
    if not departman_muduru_mu(request.user):
        return render(request, 'gorevler/yetkisiz.html')

    kayitlar = DenetimKaydi.objects.all()

    secili_kullanici = request.GET.get('kullanici', '').strip()
    if secili_kullanici:
        kayitlar = kayitlar.filter(kullanici_adi=secili_kullanici)

    kullanicilar = (
        DenetimKaydi.objects
        .order_by('kullanici_adi')
        .values_list('kullanici_adi', flat=True)
        .distinct()
    )

    return render(request, 'gorevler/denetim.html', {
        'kayitlar': kayitlar[:200],
        'kullanicilar': kullanicilar,
        'secili_kullanici': secili_kullanici,
    })


# ---------------------------------------------------------------------------
# Arşivleme (soft delete) — müdür
# ---------------------------------------------------------------------------

@login_required
def talep_sil(request, talep_id):
    talep = get_object_or_404(Talep, id=talep_id, silindi_mi=False)
    # Yatay yetki: yalnızca talebin ait olduğu departmanın müdürü arşivleyebilir.
    if not talebin_muduru_mu(request.user, talep):
        return render(request, 'gorevler/yetkisiz.html')

    if request.method == 'POST':
        talep.silindi_mi = True
        talep.silme_tarihi = timezone.now()
        talep.silen = request.user
        talep.save()
        log_yaz(request, f"Talep arsivlendi: {talep.baslik}")
        return redirect('talep_listesi')

    return render(request, 'gorevler/talep_sil.html', {'talep': talep})


# ---------------------------------------------------------------------------
# Kanban
# ---------------------------------------------------------------------------

@login_required
def kanban(request):
    talepler = gorunecek_talepler(request.user)

    return render(request, 'gorevler/kanban.html', {
        'bekliyor': talepler.filter(durum='BEKLIYOR'),
        'analizde': talepler.filter(durum='ANALIZDE'),
        'gelistiriliyor': talepler.filter(durum='GELISTIRILIYOR'),
        'testte': talepler.filter(durum='TESTTE'),
        'tamamlandi': talepler.filter(durum='TAMAMLANDI'),
    })


# ---------------------------------------------------------------------------
# Kontrol paneli
# ---------------------------------------------------------------------------

@login_required
def dashboard(request):
    talepler = gorunecek_talepler(request.user)
    bugun = timezone.now().date()

    # Reddedilen ve tamamlanan talepler "açık" sayılmaz.
    kapanmis = ['TAMAMLANDI', 'REDDEDILDI']

    toplam_list = talepler.order_by('hedef_tarih')
    acik_list = talepler.exclude(durum__in=kapanmis).order_by('hedef_tarih')
    tamamlanan_list = talepler.filter(durum='TAMAMLANDI').order_by('-guncelleme_tarihi')
    gecikmis_list = talepler.exclude(durum__in=kapanmis).filter(
        hedef_tarih__lt=bugun
    ).order_by('hedef_tarih')

    # Müdür için: atanmayı bekleyen gelen talepler.
    gelen_list = talepler.filter(atanan__isnull=True, durum='BEKLIYOR')

    return render(request, 'gorevler/dashboard.html', {
        'toplam': toplam_list.count(),
        'acik': acik_list.count(),
        'tamamlanan': tamamlanan_list.count(),
        'gecikmis': gecikmis_list.count(),
        'gelen_sayisi': gelen_list.count(),
        'toplam_list': toplam_list,
        'acik_list': acik_list,
        'tamamlanan_list': tamamlanan_list,
        'gecikmis_list': gecikmis_list,
        'yaklasanlar': acik_list.filter(hedef_tarih__gte=bugun)[:5],
    })
