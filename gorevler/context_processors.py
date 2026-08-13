from hesaplar.yetkiler import departman_muduru_mu, talep_eden_mi


def bildirimler(request):
    if request.user.is_authenticated:
        okunmamis = request.user.bildirimler.filter(okundu=False)
        return {
            'bildirim_sayisi': okunmamis.count(),
            'bildirim_listesi': okunmamis[:5],
        }
    return {}


def roller(request):
    """Tüm şablonlara rol bayraklarını sağlar (menü ve buton görünürlüğü için)."""
    if request.user.is_authenticated:
        mudur = departman_muduru_mu(request.user)
        return {
            'mudur': mudur,
            'talep_eden': talep_eden_mi(request.user),
            # Geriye dönük: eski şablonlardaki {% if takim_lideri %} = müdür.
            'takim_lideri': mudur,
        }
    return {}
