def bildirimler(request):
    if request.user.is_authenticated:
        okunmamis = request.user.bildirimler.filter(okundu=False)
        return {
            'bildirim_sayisi': okunmamis.count(),
            'bildirim_listesi': okunmamis[:5],
        }
    return {}