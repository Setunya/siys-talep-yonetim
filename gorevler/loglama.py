from .models import DenetimKaydi


def ip_al(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_yaz(request, islem):
    if request.user.is_authenticated:
        kullanici_adi = request.user.username
    else:
        kullanici_adi = 'anonim'

    DenetimKaydi.objects.create(
        kullanici_adi=kullanici_adi,
        islem=islem,
        ip_adresi=ip_al(request),
    )