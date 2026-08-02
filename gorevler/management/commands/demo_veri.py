"""
Sunum ve geliştirme için örnek (demo) veri üretir.

Kullanım:
    python manage.py demo_veri

Komut idempotenttir; tekrar çalıştırıldığında var olan kayıtları çoğaltmaz.
Rolleri, örnek kullanıcıları, birim/modül/tür kayıtlarını ve farklı durumlarda
talepleri oluşturur.
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from gorevler.models import Birim, Modul, Talep, TalepTuru


class Command(BaseCommand):
    help = "Sunum için örnek veri oluşturur."

    def handle(self, *args, **options):
        lider_grup, _ = Group.objects.get_or_create(name='TakimLideri')

        lider = self._kullanici('lider', 'Ayşe', 'Yılmaz', staff=True)
        lider.groups.add(lider_grup)
        personel1 = self._kullanici('personel1', 'Mehmet', 'Demir')
        personel2 = self._kullanici('personel2', 'Zeynep', 'Kaya')
        self.stdout.write(self.style.SUCCESS('Roller ve kullanıcılar hazır.'))

        birimler = [self._get(Birim, ad=a) for a in ['Tahsilat', 'İnsan Kaynakları', 'Muhasebe']]
        turler = [self._get(TalepTuru, ad=a) for a in ['Hata', 'Yeni Özellik', 'Bakım']]
        moduller = [self._get(Modul, ad=a) for a in ['Tahakkuk', 'Raporlama', 'Bordro']]

        if not Talep.objects.exists():
            bugun = timezone.now().date()
            ornekler = [
                ('Tahakkuk ekranı hesaplama hatası', birimler[0], turler[0], moduller[0],
                 personel1, 'YUKSEK', 'GELISTIRILIYOR', bugun + timedelta(days=2)),
                ('Bordro raporuna kıdem tazminatı sütunu', birimler[1], turler[1], moduller[2],
                 personel2, 'ORTA', 'ANALIZDE', bugun + timedelta(days=5)),
                ('Aylık raporda toplam satırı yanlış', birimler[2], turler[0], moduller[1],
                 personel1, 'YUKSEK', 'TESTTE', bugun - timedelta(days=1)),
                ('Kullanıcı yetki ekranı bakımı', birimler[0], turler[2], moduller[0],
                 personel2, 'DUSUK', 'BEKLIYOR', bugun + timedelta(days=10)),
                ('E-fatura entegrasyon talebi', birimler[2], turler[1], moduller[1],
                 personel1, 'ORTA', 'TAMAMLANDI', bugun - timedelta(days=3)),
            ]
            for baslik, birim, tur, modul, atanan, oncelik, durum, tarih in ornekler:
                Talep.objects.create(
                    baslik=baslik, aciklama='Demo amaçlı örnek talep kaydı.',
                    birim=birim, talep_turu=tur, modul=modul, hedef_surum='2026.08',
                    atanan=atanan, olusturan=lider, oncelik=oncelik, durum=durum,
                    hedef_tarih=tarih,
                )
            self.stdout.write(self.style.SUCCESS('Örnek talepler oluşturuldu.'))
        else:
            self.stdout.write('Talepler zaten mevcut, yeni kayıt eklenmedi.')

        self.stdout.write(self.style.SUCCESS(
            '\nDemo verisi hazır.\n'
            '  Takım Lideri : lider     / Parola.2026\n'
            '  Personel     : personel1 / Parola.2026\n'
            '  Personel     : personel2 / Parola.2026'
        ))

    def _kullanici(self, kullanici_adi, ad, soyad, staff=False):
        kullanici, olusturuldu = User.objects.get_or_create(
            username=kullanici_adi,
            defaults={'first_name': ad, 'last_name': soyad, 'is_staff': staff},
        )
        if olusturuldu:
            kullanici.set_password('Parola.2026')
            kullanici.save()
        return kullanici

    def _get(self, model, **kwargs):
        nesne, _ = model.objects.get_or_create(**kwargs)
        return nesne
