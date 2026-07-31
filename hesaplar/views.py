from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from gorevler.loglama import log_yaz
from datetime import timedelta
from django.utils import timezone
from gorevler.models import DenetimKaydi
def hesap_kilitli_mi(kullanici_adi):
    sinir = timezone.now() - timedelta(minutes=15)

    basarisiz = DenetimKaydi.objects.filter(
        islem=f"Basarisiz giris denemesi: {kullanici_adi}",
        tarih__gte=sinir
    ).count()

    return basarisiz >= 5

def giris(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')

        # Hesap kilitli mi kontrol et
        if hesap_kilitli_mi(kullanici_adi):
            return render(request, 'hesaplar/giris.html', {
                'hata': 'Çok fazla hatalı deneme. Hesabınız 15 dakika kilitlendi.'
            })

        kullanici = authenticate(request, username=kullanici_adi, password=sifre)

        if kullanici is not None:
            login(request, kullanici)
            log_yaz(request, "Giris yapildi")
            return redirect('talep_listesi')
        else:
            log_yaz(request, f"Basarisiz giris denemesi: {kullanici_adi}")
            return render(request, 'hesaplar/giris.html', {
                'hata': 'Kullanıcı adı veya şifre hatalı.'
            })

    return render(request, 'hesaplar/giris.html')

def cikis(request):
    log_yaz(request, "Cikis yapildi")
    logout(request)
    return redirect('giris')