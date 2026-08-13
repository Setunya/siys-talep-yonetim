"""
Rol ve yetki yardımcıları.

Roller:
- Talep Eden      : talep açar (atama yapmaz).
- Departman Müdürü: kendi departmanına gelen talebi personele atar veya
                    gerekçeyle reddeder; tamamlananı onaylar; denetim görür.
- Personel        : kendisine atanan işi yürütür.
"""


def departman_muduru_mu(user):
    """Üst yetki: atama, reddetme, onaylama, arşivleme, denetim."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='DepartmanMuduru').exists()


def talep_eden_mi(user):
    """Talep açma yetkisi olan rol."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='TalepEden').exists()


# Geriye dönük uyumluluk: eski kodda "takım lideri" = üst yetki.
# Artık üst yetki "departman müdürü" olduğundan buna yönlendiriyoruz.
def takim_lideri_mi(user):
    return departman_muduru_mu(user)


def yonettigi_departman_idleri(user):
    """Müdürün yönettiği departmanların id listesi (talep yönlendirme için)."""
    from gorevler.models import Departman
    if user.is_superuser:
        return list(Departman.objects.values_list('id', flat=True))
    return list(
        Departman.objects.filter(mudur=user).values_list('id', flat=True)
    )
