# ============================================================
# models.py — Veritabanı tablolarının tanımlandığı dosya
# Her "class", veritabanında bir TABLO oluşturur.
# Her satır (ad = models.XXX), o tabloda bir SÜTUN oluşturur.
# ============================================================

# Django'nun veritabanı araç kutusunu getiriyoruz.
# CharField, ForeignKey gibi parçalar bunun içinde.
from django.db import models

# Django'nun hazır Kullanıcı tablosunu getiriyoruz.
# "Atanan kişi", "oluşturan kişi" gibi alanlar buna bağlanacak.
from django.contrib.auth.models import User

# Tarih/saat işlemleri için (gecikme hesabı vb. ileride lazım olacak).
from django.utils import timezone


# ============================================================
# TABLO 1: BİRİM
# Talep gönderen daireleri tutar. Örn: Tahsilat, İnsan Kaynakları
# ============================================================
class Birim(models.Model):
    # Birimin adı. CharField = kısa metin. max_length zorunlu.
    # unique=True → aynı birim adı iki kez girilemez.
    ad = models.CharField("Birim Adı", max_length=150, unique=True)

    # TextField = uzun metin. blank=True → boş bırakılabilir.
    aciklama = models.TextField("Açıklama", blank=True)

    # BooleanField = evet/hayır. default=True → yeni kayıt aktif gelir.
    aktif = models.BooleanField("Aktif", default=True)

    # class Meta → tablonun kendi ayarları (sütun değil).
    class Meta:
        verbose_name = "Birim"            # Panelde tekil ad
        verbose_name_plural = "Birimler"  # Panelde çoğul ad
        ordering = ['ad']                 # Ada göre sırala

    # Bu kayıt yazıya döküldüğünde ne görünsün?
    # Olmasa "Birim object (1)" görürdük; şimdi "Tahsilat" göreceğiz.
    def __str__(self):
        return self.ad


# ============================================================
# TABLO 2: TALEP TÜRÜ
# Talebin ne tür olduğu. Örn: Yeni Özellik, Hata, Bakım
# ============================================================
class TalepTuru(models.Model):
    ad = models.CharField("Talep Türü", max_length=100, unique=True)
    aciklama = models.TextField("Açıklama", blank=True)
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Talep Türü"
        verbose_name_plural = "Talep Türleri"
        ordering = ['ad']

    def __str__(self):
        return self.ad


# ============================================================
# TABLO 3: MODÜL
# Talebin ait olduğu yazılım modülü. Örn: Tahakkuk, Raporlama
# ============================================================
class Modul(models.Model):
    ad = models.CharField("Modül Adı", max_length=100, unique=True)
    aciklama = models.TextField("Açıklama", blank=True)
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Modül"
        verbose_name_plural = "Modüller"
        ordering = ['ad']

    def __str__(self):
        return self.ad


# ============================================================
# TABLO: DEPARTMAN
# Talebin yönlendirileceği birim. Her departmanın bir müdürü vardır;
# bir talep bir departmana açılınca otomatik o departmanın müdürüne düşer.
# ============================================================
class Departman(models.Model):
    ad = models.CharField("Departman Adı", max_length=120, unique=True)
    mudur = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='yonettigi_departmanlar', verbose_name="Departman Müdürü"
    )
    aktif = models.BooleanField("Aktif", default=True)

    class Meta:
        verbose_name = "Departman"
        verbose_name_plural = "Departmanlar"
        ordering = ['ad']

    def __str__(self):
        return self.ad


# ============================================================
# TABLO 4: TALEP  (Sistemin ana tablosu)
# Yukarıdaki üç tabloya ve Kullanıcı tablosuna bağlanır.
# ============================================================
class Talep(models.Model):

    # --- SEÇENEK LİSTELERİ ---
    # TextChoices → sabit seçenek listesi.
    # Soldaki (BEKLIYOR) veritabanına yazılan değer.
    # Sağdaki ('Bekliyor') ekranda görünen etiket.
    # Bu sayede durum alanına rastgele metin yazılamaz.
    class Durum(models.TextChoices):
        BEKLIYOR = 'BEKLIYOR', 'Bekliyor'
        ANALIZDE = 'ANALIZDE', 'Analizde'
        GELISTIRILIYOR = 'GELISTIRILIYOR', 'Geliştiriliyor'
        TESTTE = 'TESTTE', 'Testte'
        TAMAMLANDI = 'TAMAMLANDI', 'Tamamlandı'
        REDDEDILDI = 'REDDEDILDI', 'Reddedildi'

    class Oncelik(models.TextChoices):
        DUSUK = 'DUSUK', 'Düşük'
        ORTA = 'ORTA', 'Orta'
        YUKSEK = 'YUKSEK', 'Yüksek'

    # --- TEMEL BİLGİLER ---
    baslik = models.CharField("Başlık", max_length=200)
    aciklama = models.TextField("Açıklama", blank=True)

    # --- İLİŞKİLER (ForeignKey = başka tabloya bağlantı) ---
    # Her talep BİR birime aittir. on_delete=PROTECT →
    # o birime bağlı talep varsa, birim silinemez (veri korunur).
    birim = models.ForeignKey(
        Birim, on_delete=models.PROTECT, verbose_name="Talep Eden Birim"
    )
    talep_turu = models.ForeignKey(
        TalepTuru, on_delete=models.PROTECT, verbose_name="Talep Türü"
    )
    modul = models.ForeignKey(
        Modul, on_delete=models.PROTECT, verbose_name="İlgili Modül"
    )
    # Talebin yönlendirileceği departman. Talep açılınca otomatik bu
    # departmanın müdürünün "Gelen Talepler" kutusuna düşer.
    departman = models.ForeignKey(
        Departman, on_delete=models.PROTECT, null=True, blank=True,
        related_name='talepler', verbose_name="İlgili Departman"
    )

    # Hedef sürüm. Örn: "2026.07". Kısa metin olarak tutuyoruz.
    hedef_surum = models.CharField(
        "Hedef Sürüm", max_length=20, blank=True, help_text="Örn: 2026.07"
    )

    # --- KİŞİLER (User tablosuna bağlanır) ---
    # related_name → ters yönden erişim adı.
    # Aynı User'a iki alan bağlandığı için farklı isim şart,
    # yoksa Django hangisini kastettiğini bilemez.
    # Talep önce ATANMAMIŞ gelir; departman müdürü bir personele atayınca dolar.
    atanan = models.ForeignKey(
        User, on_delete=models.PROTECT, null=True, blank=True,
        related_name='atanan_talepler', verbose_name="Atanan Personel"
    )
    olusturan = models.ForeignKey(
        User, on_delete=models.PROTECT,
        related_name='olusturulan_talepler', verbose_name="Oluşturan"
    )

    # --- DURUM VE ÖNCELİK ---
    # choices=... → yukarıdaki listeden seçilir.
    # default=... → yeni talep bu değerle başlar.
    oncelik = models.CharField(
        "Öncelik", max_length=10,
        choices=Oncelik.choices, default=Oncelik.ORTA
    )
    durum = models.CharField(
        "Durum", max_length=15,
        choices=Durum.choices, default=Durum.BEKLIYOR
    )

    # --- REDDETME (departman müdürü talebi gerekçeyle reddedebilir) ---
    red_gerekce = models.TextField("Red Gerekçesi", blank=True)
    red_eden = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reddettigi_talepler', verbose_name="Reddeden"
    )
    red_tarihi = models.DateTimeField(null=True, blank=True)

    # --- TARİHLER ---
    # DateField = sadece tarih (saat yok).
    hedef_tarih = models.DateField("Hedef Tarih", null=True, blank=True)

    # null=True → veritabanında boş olabilir. Talep kapanınca dolar.
    tamamlanma_tarihi = models.DateTimeField(null=True, blank=True)

    # Talebi kapatan (onaylayan) kişi. SET_NULL → o kullanıcı
    # silinse bile talep kalır, sadece bu alan boşalır.
    onaylayan = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='onayladigi_talepler', verbose_name="Onaylayan"
    )

    # --- YUMUŞAK SİLME (soft delete) ---
    # Kayıt gerçekten silinmez; "arşivlendi" olarak işaretlenir.
    # Kamu kurumunda kayıt bütünlüğü için gerekli.
    silindi_mi = models.BooleanField("Arşivlendi", default=False)
    silme_tarihi = models.DateTimeField(null=True, blank=True)
    silen = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sildigi_talepler'
    )

    # --- OTOMATİK TARİHLER ---
    # auto_now_add → kayıt İLK oluşturulduğunda tarihi yazar, bir daha değişmez.
    olusturma_tarihi = models.DateTimeField(auto_now_add=True)
    # auto_now → her kaydetmede güncellenir.
    guncelleme_tarihi = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Talep"
        verbose_name_plural = "Talepler"
        ordering = ['-olusturma_tarihi']  # En yeni talep en üstte

    def __str__(self):
        # Örn: "Tahakkuk ekranı hatası — Tahsilat (#3)"
        return f"{self.baslik} — {self.birim.ad}"

    # @property → veritabanı sütunu DEĞİL, hesaplanan değer.
    # Her çağrıldığında son tarihi bugünle karşılaştırıp cevap üretir.
    @property
    def gecikmis_mi(self):
        if self.durum == self.Durum.TAMAMLANDI:
            return False
        if not self.hedef_tarih:
            return False
        return self.hedef_tarih < timezone.now().date()

class Yorum(models.Model):
    talep = models.ForeignKey(
        Talep, on_delete=models.CASCADE,
        related_name='yorumlar', verbose_name="Talep"
    )
    yazan = models.ForeignKey(
        User, on_delete=models.PROTECT, verbose_name="Yazan"
    )
    metin = models.TextField("Yorum")
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Yorum"
        verbose_name_plural = "Yorumlar"
        ordering = ['tarih']

    def __str__(self):
        return f"{self.yazan.username} - {self.talep.baslik}"


class Bildirim(models.Model):
    kullanici = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='bildirimler', verbose_name="Kullanıcı"
    )
    mesaj = models.CharField("Mesaj", max_length=255)
    talep = models.ForeignKey(
        Talep, on_delete=models.CASCADE, null=True, blank=True
    )
    okundu = models.BooleanField("Okundu", default=False)
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Bildirim"
        verbose_name_plural = "Bildirimler"
        ordering = ['-tarih']

    def __str__(self):
        return f"{self.kullanici.username} - {self.mesaj}"

class DenetimKaydi(models.Model):
    kullanici_adi = models.CharField("Kullanıcı", max_length=150)
    islem = models.CharField("İşlem", max_length=255)
    ip_adresi = models.GenericIPAddressField("IP Adresi", null=True, blank=True)
    tarih = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Denetim Kaydı"
        verbose_name_plural = "Denetim Kayıtları"
        ordering = ['-tarih']

    def __str__(self):
        return f"{self.tarih:%d.%m.%Y %H:%M} - {self.kullanici_adi} - {self.islem}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("Denetim kayıtları değiştirilemez.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Denetim kayıtları silinemez.")