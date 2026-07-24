def takim_lideri_mi(user):
    if user.is_superuser:
        return True
    return user.groups.filter(name='TakimLideri').exists()