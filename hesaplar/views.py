from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout


def giris(request):
    if request.method == 'POST':
        kullanici_adi = request.POST.get('username')
        sifre = request.POST.get('password')

        kullanici = authenticate(request, username=kullanici_adi, password=sifre)

        if kullanici is not None:
            login(request, kullanici)
            return redirect('talep_listesi')
        else:
            return render(request, 'hesaplar/giris.html', {
                'hata': 'Kullanıcı adı veya şifre hatalı.'
            })

    return render(request, 'hesaplar/giris.html')


def cikis(request):
    logout(request)
    return redirect('giris')