"""
Sunum ve geliştirme için örnek (demo) veri üretir.

Kullanım:
    python manage.py demo_veri                     # rastgele parola üretir
    python manage.py demo_veri --parola <parola>   # parolayı siz belirlersiniz

Parola kaynak kodda tutulmaz; yalnızca yeni oluşturulan hesaplara atanır
ve komut çıktısında bir kez gösterilir.

Komut idempotenttir; tekrar çalıştırıldığında kayıtları çoğaltmaz.
Rolleri (Talep Eden / Departman Müdürü / Personel), departmanları,
kullanıcıları ve farklı durumlarda talepleri (gelen, atanmış, tamamlanmış,
reddedilmiş) oluşturur.
"""

import secrets
from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from gorevler.models import Birim, Departman, Modul, Talep, TalepTuru


class Command(BaseCommand):
    help = "Sunum için örnek veri oluşturur."

    def add_arguments(self, parser):
        parser.add_argument(
            '--parola',
            help='Demo hesaplarının parolası (verilmezse rastgele üretilir).',
        )

    def handle(self, *args, **options):
        self.parola = options['parola'] or secrets.token_urlsafe(9)
        self.yeni_hesap = False

        # --- Roller ---
        g_mudur, _ = Group.objects.get_or_create(name='DepartmanMuduru')
        g_eden, _ = Group.objects.get_or_create(name='TalepEden')
        g_personel, _ = Group.objects.get_or_create(name='Personel')

        # --- Kullanıcılar ---
        lider = self._kullanici('lider', 'Ayşe', 'Yılmaz', staff=True)
        lider.groups.add(g_mudur)
        mudur2 = self._kullanici('mudur2', 'Can', 'Aydın', staff=True)
        mudur2.groups.add(g_mudur)
        talepeden = self._kullanici('talepeden', 'Elif', 'Şahin')
        talepeden.groups.add(g_eden)
        personel1 = self._kullanici('personel1', 'Mehmet', 'Demir')
        personel1.groups.add(g_personel)
        personel2 = self._kullanici('personel2', 'Zeynep', 'Kaya')
        personel2.groups.add(g_personel)
        self.stdout.write(self.style.SUCCESS('Roller ve kullanıcılar hazır.'))

        # --- Departmanlar (her birinin bir müdürü var) ---
        dep_yazilim = self._get(Departman, ad='Yazılım Geliştirme',
                                defaults={'mudur': lider})
        dep_rapor = self._get(Departman, ad='Raporlama Sistemleri',
                              defaults={'mudur': mudur2})
        self._mudur_ata(dep_yazilim, lider)
        self._mudur_ata(dep_rapor, mudur2)

        # --- Referans kayıtlar ---
        birimler = [self._get(Birim, ad=a) for a in ['Tahsilat', 'İnsan Kaynakları', 'Muhasebe']]
        turler = [self._get(TalepTuru, ad=a) for a in ['Hata', 'Yeni Özellik', 'Bakım']]

        # Her modül bir departmana bağlıdır; talep bu modüle açılınca departman
        # (ve dolayısıyla müdür) otomatik belirlenir.
        modul_departman = {
            'Tahakkuk': dep_yazilim,
            'Raporlama': dep_rapor,
            'Bordro': dep_yazilim,
        }
        moduller = []
        for ad, dep in modul_departman.items():
            m = self._get(Modul, ad=ad)
            if m.departman_id != dep.id:
                m.departman = dep
                m.save()
            moduller.append(m)

        bugun = timezone.now().date()

        # (baslik, birim, tur, modul, departman, atanan, durum, oncelik, gun_farki)
        ornekler = [
            # Gelen (atanmamış) — müdürün "Gelen Talepler" kutusuna düşer
            ('Kullanıcı yetki ekranı bakımı', birimler[0], turler[2], moduller[0],
             dep_yazilim, None, 'BEKLIYOR', 'DUSUK', 10),
            ('Aylık gelir raporu yeni filtre', birimler[2], turler[1], moduller[1],
             dep_rapor, None, 'BEKLIYOR', 'ORTA', 8),
            # Atanmış — süreçte
            ('Tahakkuk ekranı hesaplama hatası', birimler[0], turler[0], moduller[0],
             dep_yazilim, personel1, 'GELISTIRILIYOR', 'YUKSEK', 2),
            ('Bordro raporuna kıdem tazminatı sütunu', birimler[1], turler[1], moduller[2],
             dep_yazilim, personel2, 'ANALIZDE', 'ORTA', 5),
            ('Aylık raporda toplam satırı yanlış', birimler[2], turler[0], moduller[1],
             dep_rapor, personel1, 'TESTTE', 'YUKSEK', -1),
            # Tamamlanmış
            ('E-fatura entegrasyon talebi', birimler[2], turler[1], moduller[1],
             dep_rapor, personel1, 'TAMAMLANDI', 'ORTA', -3),
        ]
        for baslik, birim, tur, modul, dep, atanan, durum, oncelik, gun in ornekler:
            talep, olusturuldu = Talep.objects.get_or_create(
                baslik=baslik,
                defaults=dict(
                    aciklama='Demo amaçlı örnek talep kaydı.',
                    birim=birim, talep_turu=tur, modul=modul, departman=dep,
                    atanan=atanan, olusturan=talepeden, oncelik=oncelik,
                    durum=durum, hedef_surum='2026.08',
                    hedef_tarih=bugun + timedelta(days=gun),
                ),
            )
            if olusturuldu and durum == 'TAMAMLANDI':
                talep.onaylayan = dep.mudur
                talep.save()

        # Reddedilmiş örnek
        red, olusturuldu = Talep.objects.get_or_create(
            baslik='Ana sayfaya reklam alanı eklensin',
            defaults=dict(
                aciklama='Demo amaçlı örnek talep kaydı.',
                birim=birimler[0], talep_turu=turler[1], modul=moduller[1],
                departman=dep_rapor, atanan=None, olusturan=talepeden,
                oncelik='DUSUK', durum='REDDEDILDI', hedef_surum='2026.08',
                hedef_tarih=bugun + timedelta(days=4),
                red_eden=mudur2, red_gerekce='Kurumsal politika gereği reklam alanı eklenmemektedir.',
                red_tarihi=timezone.now(),
            ),
        )
        self.stdout.write(self.style.SUCCESS('Departmanlar ve örnek talepler hazır.'))

        if self.yeni_hesap:
            parola_satiri = f'Yeni hesapların parolası: {self.parola}'
        else:
            parola_satiri = 'Hesaplar zaten vardı; parolaları değiştirilmedi.'
        self.stdout.write(self.style.SUCCESS(
            f'\nDemo verisi hazır. {parola_satiri}\n'
            '  Departman Müdürü : lider      (Yazılım Geliştirme)\n'
            '  Departman Müdürü : mudur2     (Raporlama Sistemleri)\n'
            '  Talep Eden       : talepeden\n'
            '  Personel         : personel1\n'
            '  Personel         : personel2'
        ))

    def _kullanici(self, kullanici_adi, ad, soyad, staff=False):
        kullanici, olusturuldu = User.objects.get_or_create(
            username=kullanici_adi,
            defaults={'first_name': ad, 'last_name': soyad, 'is_staff': staff},
        )
        if olusturuldu:
            kullanici.set_password(self.parola)
            kullanici.save()
            self.yeni_hesap = True
        return kullanici

    def _mudur_ata(self, departman, mudur):
        if departman.mudur_id != mudur.id:
            departman.mudur = mudur
            departman.save()

    def _get(self, model, defaults=None, **kwargs):
        nesne, _ = model.objects.get_or_create(defaults=defaults or {}, **kwargs)
        return nesne
