"""
Otomatik testler — işlevsel ve güvenlik senaryoları.

Her test sınıfı bir güvenlik/iş kuralını doğrular:
- Yatay yetki (IDOR), dikey yetki (rol)
- Kurallı durum geçişleri ve onay yetkisi
- Hesap kilitleme (kaba kuvvet koruması)
- Denetim kaydının değiştirilemezliği
- Yumuşak silme (soft delete)
- XSS kaçışı ve parola saklama
"""

from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Birim, DenetimKaydi, Modul, Talep, TalepTuru


class TemelKurulum(TestCase):
    def setUp(self):
        self.lider_grup = Group.objects.create(name='TakimLideri')

        self.lider = User.objects.create_user('lider', password='Parola.2026')
        self.lider.groups.add(self.lider_grup)
        self.personel_a = User.objects.create_user('pa', password='Parola.2026')
        self.personel_b = User.objects.create_user('pb', password='Parola.2026')

        self.birim = Birim.objects.create(ad='Tahsilat')
        self.tur = TalepTuru.objects.create(ad='Hata')
        self.modul = Modul.objects.create(ad='Raporlama')

        self.talep_a = self._talep(self.personel_a, 'A talebi')
        self.talep_b = self._talep(self.personel_b, 'B talebi')

    def _talep(self, atanan, baslik, durum='BEKLIYOR'):
        return Talep.objects.create(
            baslik=baslik, birim=self.birim, talep_turu=self.tur, modul=self.modul,
            atanan=atanan, olusturan=self.lider, durum=durum, oncelik='ORTA',
            hedef_tarih=timezone.now().date() + timedelta(days=3),
        )


class YetkiTest(TemelKurulum):
    def test_idor_baskasinin_talebine_erisim_engellenir(self):
        """Personel, kendisine ait olmayan talebe erişemez (IDOR koruması)."""
        self.client.login(username='pa', password='Parola.2026')
        yanit = self.client.get(reverse('talep_detay', args=[self.talep_b.id]))
        self.assertTemplateUsed(yanit, 'gorevler/yetkisiz.html')

    def test_personel_kendi_talebini_gorebilir(self):
        self.client.login(username='pa', password='Parola.2026')
        yanit = self.client.get(reverse('talep_detay', args=[self.talep_a.id]))
        self.assertTemplateUsed(yanit, 'gorevler/talep_detay.html')

    def test_personel_talep_olusturamaz(self):
        """Dikey yetki: talep oluşturma yalnızca takım liderine açıktır."""
        self.client.login(username='pa', password='Parola.2026')
        yanit = self.client.get(reverse('talep_olustur'))
        self.assertTemplateUsed(yanit, 'gorevler/yetkisiz.html')

    def test_personel_yalnizca_kendi_taleplerini_listeler(self):
        self.client.login(username='pa', password='Parola.2026')
        yanit = self.client.get(reverse('talep_listesi'))
        self.assertContains(yanit, 'A talebi')
        self.assertNotContains(yanit, 'B talebi')

    def test_gecersiz_talep_id_404_doner(self):
        self.client.login(username='lider', password='Parola.2026')
        yanit = self.client.get(reverse('talep_detay', args=[999999]))
        self.assertEqual(yanit.status_code, 404)


class DurumAkisiTest(TemelKurulum):
    def test_gecersiz_gecis_reddedilir(self):
        """BEKLIYOR -> TAMAMLANDI doğrudan geçiş kurallara aykırıdır."""
        self.client.login(username='lider', password='Parola.2026')
        self.client.post(reverse('durum_degistir', args=[self.talep_a.id]), {'durum': 'TAMAMLANDI'})
        self.talep_a.refresh_from_db()
        self.assertEqual(self.talep_a.durum, 'BEKLIYOR')

    def test_personel_tamamlayamaz(self):
        """Onay (TAMAMLANDI) yetkisi yalnızca takım liderinindir."""
        talep = self._talep(self.personel_a, 'Testte talep', durum='TESTTE')
        self.client.login(username='pa', password='Parola.2026')
        self.client.post(reverse('durum_degistir', args=[talep.id]), {'durum': 'TAMAMLANDI'})
        talep.refresh_from_db()
        self.assertEqual(talep.durum, 'TESTTE')

    def test_lider_testten_tamamlar(self):
        talep = self._talep(self.personel_a, 'Onaylanacak', durum='TESTTE')
        self.client.login(username='lider', password='Parola.2026')
        self.client.post(reverse('durum_degistir', args=[talep.id]), {'durum': 'TAMAMLANDI'})
        talep.refresh_from_db()
        self.assertEqual(talep.durum, 'TAMAMLANDI')


class SoftDeleteTest(TemelKurulum):
    def test_arsivlenen_talep_listeden_cikar_veritabaninda_kalir(self):
        self.client.login(username='lider', password='Parola.2026')
        self.client.post(reverse('talep_sil', args=[self.talep_a.id]))
        self.talep_a.refresh_from_db()
        self.assertTrue(self.talep_a.silindi_mi)
        self.assertTrue(Talep.objects.filter(id=self.talep_a.id).exists())
        yanit = self.client.get(reverse('talep_listesi'))
        self.assertNotContains(yanit, 'A talebi')


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
        # Kilitliyken doğru parola bile kabul edilmez.
        self.client.post(giris, {'username': 'pa', 'password': 'Parola.2026'})
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
        self.client.login(username='pa', password='Parola.2026')
        yanit = self.client.get(reverse('talep_detay', args=[self.talep_a.id]))
        self.assertNotContains(yanit, '<script>alert(1)</script>')

    def test_parola_hashlenir(self):
        self.assertTrue(self.personel_a.password.startswith('pbkdf2_'))
        self.assertNotIn('Parola.2026', self.personel_a.password)
