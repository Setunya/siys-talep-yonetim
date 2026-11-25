"""
Otomatik testler — işlevsel ve güvenlik senaryoları (iki katmanlı akış).

Roller: Talep Eden → Departman Müdürü → Personel.
Kapsanan konular:
- Yatay yetki (IDOR) ve çapraz departman izolasyonu
- Dikey yetki (talep açma / atama / reddetme / onay)
- Otomatik yönlendirme, atama ve gerekçeli reddetme
- Kurallı durum geçişleri
- Hesap kilitleme, denetim değiştirilemezliği, soft delete, XSS, parola
"""

import secrets
from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Birim, Departman, DenetimKaydi, Modul, Talep, TalepTuru

# Test hesapları için her çalıştırmada rastgele parola; kaynak kodda sabit parola yok.
PAROLA = secrets.token_urlsafe(12)


class TemelKurulum(TestCase):
    def setUp(self):
        Group.objects.create(name='DepartmanMuduru')
        Group.objects.create(name='TalepEden')
        Group.objects.create(name='Personel')

        self.mudur = self._kullanici('mudur', 'DepartmanMuduru')
        self.mudur2 = self._kullanici('mudur2', 'DepartmanMuduru')
        self.eden = self._kullanici('eden', 'TalepEden')
        self.personel_a = self._kullanici('pa', 'Personel')
        self.personel_b = self._kullanici('pb', 'Personel')

        self.birim = Birim.objects.create(ad='Tahsilat')
        self.tur = TalepTuru.objects.create(ad='Hata')
        self.modul = Modul.objects.create(ad='Raporlama')
        self.dep = Departman.objects.create(ad='Yazılım', mudur=self.mudur)
        self.dep2 = Departman.objects.create(ad='Raporlama', mudur=self.mudur2)

        # Atanmış talepler (mudur'un departmanı)
        self.talep_a = self._talep('A talebi', atanan=self.personel_a)
        self.talep_b = self._talep('B talebi', atanan=self.personel_b)
        # Gelen (atanmamış) talep
        self.gelen = self._talep('Gelen talep', atanan=None)

    def _kullanici(self, kad, grup):
        u = User.objects.create_user(kad, password=PAROLA)
        u.groups.add(Group.objects.get(name=grup))
        return u

    def _talep(self, baslik, atanan=None, durum='BEKLIYOR', departman=None):
        return Talep.objects.create(
            baslik=baslik, birim=self.birim, talep_turu=self.tur, modul=self.modul,
            departman=departman or self.dep, atanan=atanan, olusturan=self.eden,
            durum=durum, oncelik='ORTA',
            hedef_tarih=timezone.now().date() + timedelta(days=3),
        )


class YetkiTest(TemelKurulum):
    def test_idor_baskasinin_talebine_erisim_engellenir(self):
        self.client.login(username='pa', password=PAROLA)
        yanit = self.client.get(reverse('talep_detay', args=[self.talep_b.id]))
        self.assertTemplateUsed(yanit, 'gorevler/yetkisiz.html')

    def test_personel_kendi_talebini_gorebilir(self):
        self.client.login(username='pa', password=PAROLA)
        yanit = self.client.get(reverse('talep_detay', args=[self.talep_a.id]))
        self.assertTemplateUsed(yanit, 'gorevler/talep_detay.html')

    def test_personel_talep_olusturamaz(self):
        self.client.login(username='pa', password=PAROLA)
        yanit = self.client.get(reverse('talep_olustur'))
        self.assertTemplateUsed(yanit, 'gorevler/yetkisiz.html')

    def test_talep_eden_talep_olusturabilir(self):
        self.client.login(username='eden', password=PAROLA)
        yanit = self.client.get(reverse('talep_olustur'))
        self.assertTemplateUsed(yanit, 'gorevler/talep_form.html')

    def test_mudur_departmanindaki_talepleri_gorur(self):
        self.client.login(username='mudur', password=PAROLA)
        yanit = self.client.get(reverse('talep_listesi'))
        self.assertContains(yanit, 'A talebi')

    def test_capraz_departman_izolasyonu(self):
        """Bir müdür başka departmanın talebine erişemez."""
        baska = self._talep('Başka dep talebi', atanan=None, departman=self.dep2)
        self.client.login(username='mudur', password=PAROLA)
        yanit = self.client.get(reverse('talep_detay', args=[baska.id]))
        self.assertTemplateUsed(yanit, 'gorevler/yetkisiz.html')

    def test_gecersiz_talep_id_404(self):
        self.client.login(username='mudur', password=PAROLA)
        yanit = self.client.get(reverse('talep_detay', args=[999999]))
        self.assertEqual(yanit.status_code, 404)


class AtamaRedTest(TemelKurulum):
    def test_mudur_talebi_personele_atar(self):
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('talep_ata', args=[self.gelen.id]),
                         {'atanan': self.personel_a.id})
        self.gelen.refresh_from_db()
        self.assertEqual(self.gelen.atanan, self.personel_a)

    def test_baska_mudur_atayamaz(self):
        self.client.login(username='mudur2', password=PAROLA)
        self.client.post(reverse('talep_ata', args=[self.gelen.id]),
                         {'atanan': self.personel_a.id})
        self.gelen.refresh_from_db()
        self.assertIsNone(self.gelen.atanan)

    def test_reddetme_gerekce_zorunlu(self):
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('talep_reddet', args=[self.gelen.id]),
                         {'red_gerekce': ''})
        self.gelen.refresh_from_db()
        self.assertEqual(self.gelen.durum, 'BEKLIYOR')

    def test_gerekceli_reddetme(self):
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('talep_reddet', args=[self.gelen.id]),
                         {'red_gerekce': 'Bütçe yetersiz.'})
        self.gelen.refresh_from_db()
        self.assertEqual(self.gelen.durum, 'REDDEDILDI')
        self.assertEqual(self.gelen.red_eden, self.mudur)
        self.assertTrue(self.gelen.red_gerekce)


class DurumAkisiTest(TemelKurulum):
    def test_gecersiz_gecis_reddedilir(self):
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('durum_degistir', args=[self.talep_a.id]),
                         {'durum': 'TAMAMLANDI'})
        self.talep_a.refresh_from_db()
        self.assertEqual(self.talep_a.durum, 'BEKLIYOR')

    def test_atanmamis_talep_ilerletilemez(self):
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('durum_degistir', args=[self.gelen.id]),
                         {'durum': 'ANALIZDE'})
        self.gelen.refresh_from_db()
        self.assertEqual(self.gelen.durum, 'BEKLIYOR')

    def test_personel_tamamlayamaz(self):
        talep = self._talep('Testte', atanan=self.personel_a, durum='TESTTE')
        self.client.login(username='pa', password=PAROLA)
        self.client.post(reverse('durum_degistir', args=[talep.id]),
                         {'durum': 'TAMAMLANDI'})
        talep.refresh_from_db()
        self.assertEqual(talep.durum, 'TESTTE')

    def test_mudur_testten_tamamlar(self):
        talep = self._talep('Onaylanacak', atanan=self.personel_a, durum='TESTTE')
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('durum_degistir', args=[talep.id]),
                         {'durum': 'TAMAMLANDI'})
        talep.refresh_from_db()
        self.assertEqual(talep.durum, 'TAMAMLANDI')


class SoftDeleteTest(TemelKurulum):
    def test_arsivlenen_talep_listeden_cikar_veritabaninda_kalir(self):
        self.client.login(username='mudur', password=PAROLA)
        self.client.post(reverse('talep_sil', args=[self.talep_a.id]))
        self.talep_a.refresh_from_db()
        self.assertTrue(self.talep_a.silindi_mi)
        self.assertTrue(Talep.objects.filter(id=self.talep_a.id).exists())
        yanit = self.client.get(reverse('talep_listesi'))
        self.assertNotContains(yanit, 'A talebi')

    def test_baska_departmanin_muduru_arsivleyemez(self):
        # IDOR: mudur2, mudur'un departmanındaki talebi arşivleyememeli.
        self.client.login(username='mudur2', password=PAROLA)
        self.client.post(reverse('talep_sil', args=[self.talep_a.id]))
        self.talep_a.refresh_from_db()
        self.assertFalse(self.talep_a.silindi_mi)


class DenetimKaydiTest(TemelKurulum):
    def test_denetim_kaydi_degistirilemez(self):
        kayit = DenetimKaydi.objects.create(kullanici_adi='x', islem='deneme')
        kayit.islem = 'degisti'
        with self.assertRaises(ValueError):
            kayit.save()

    def test_denetim_kaydi_silinemez(self):
        kayit = DenetimKaydi.objects.create(kullanici_adi='x', islem='deneme')
        with self.assertRaises(ValueError):
            kayit.delete()


class GirisGuvenligiTest(TemelKurulum):
    def test_bes_hatali_denemede_hesap_kilitlenir(self):
        giris = reverse('giris')
        for _ in range(5):
            self.client.post(giris, {'username': 'pa', 'password': 'yanlis'})
        from hesaplar.views import hesap_kilitli_mi
        self.assertTrue(hesap_kilitli_mi('pa'))
        self.client.post(giris, {'username': 'pa', 'password': PAROLA})
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_hata_mesaji_ayni(self):
        giris = reverse('giris')
        y1 = self.client.post(giris, {'username': 'yok', 'password': 'x'})
        y2 = self.client.post(giris, {'username': 'pa', 'password': 'yanlis'})
        self.assertContains(y1, 'Kullanıcı adı veya şifre hatalı')
        self.assertContains(y2, 'Kullanıcı adı veya şifre hatalı')


class GuvenlikGenelTest(TemelKurulum):
    def test_oturumsuz_erisim_girise_yonlendirir(self):
        yanit = self.client.get(reverse('talep_listesi'))
        self.assertEqual(yanit.status_code, 302)
        self.assertIn('/giris/', yanit.url)

    def test_xss_betik_kacislanir(self):
        self.talep_a.aciklama = '<script>alert(1)</script>'
        self.talep_a.save()
        self.client.login(username='pa', password=PAROLA)
        yanit = self.client.get(reverse('talep_detay', args=[self.talep_a.id]))
        self.assertNotContains(yanit, '<script>alert(1)</script>')

    def test_parola_hashlenir(self):
        self.assertTrue(self.personel_a.password.startswith('pbkdf2_'))
        self.assertNotIn(PAROLA, self.personel_a.password)
