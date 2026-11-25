# SİYS — Sistem İstek ve Talep Yönetim Sistemi

Kurumsal bir yazılım biriminin, iç birimlerden gelen talepleri (hata, yeni özellik,
bakım vb.) uçtan uca yönettiği web tabanlı bir görev/talep takip sistemidir. Güvenlik
(kimlik doğrulama, rol ve kayıt bazlı yetkilendirme, denetim izi) tasarımın temel
bileşenidir.

## Özellikler

- **Kimlik doğrulama:** Oturum tabanlı giriş/çıkış, hesap kilitleme (5 hatalı denemede 15 dk).
- **Üç rol:** Talep Eden, Departman Müdürü ve Personel.
- **Modüle göre otomatik yönlendirme:** Talep eden yalnızca ilgili modülü seçer; sistem
  talebi o modülün bağlı olduğu departmanın müdürüne iletir ve müdüre bildirim gönderir.
- **Atama ve gerekçeli reddetme:** Müdür gelen talebi bir personele atar ya da gerekçe
  yazarak reddeder; reddedilen talepler ayrı listelenir.
- **İki katmanlı yetkilendirme:**
  - *Dikey (rol):* Her işlem yalnızca yetkili role açıktır; denetim hem arayüzde hem sunucuda yapılır.
  - *Yatay (sahiplik / IDOR koruması):* Talep Eden yalnızca kendi açtığı, Personel yalnızca
    kendisine atanan, Müdür yalnızca kendi departmanının taleplerini görür.
- **Talep yönetimi:** Oluşturma, listeleme, detay, arama + filtreleme + sayfalama.
- **Kurallı durum akışı:** Bekliyor → Analizde → Geliştiriliyor → Testte → Tamamlandı
  (yalnızca tanımlı geçişlere izin verilir, Testte'den Geliştiriliyor'a geri dönülebilir;
  atanmamış talep ilerletilemez; "Tamamlandı" onayı yalnızca departman müdürüne açıktır).
- **Yorum/mesajlaşma:** Talep içi yorumlar ve ilgili tarafa bildirim.
- **Uygulama içi bildirim:** Zil, okunmamış sayacı ve bildirim listesi.
- **Denetim günlüğü:** Değiştirilemez (append-only) işlem kaydı; kim/ne zaman/hangi IP.
- **Yumuşak silme (soft delete):** Talepler silinmez, arşivlenir; kayıt bütünlüğü korunur.
- **Kanban panosu ve kontrol paneli:** Durum bazlı görünüm ve özet sayaçlar.

## Teknolojiler

| Katman | Teknoloji |
|---|---|
| Dil | Python 3.13 |
| Çatı | Django 6.0 |
| Veritabanı | SQLite |
| Arayüz | Django şablonları + Bootstrap 5 + Bootstrap Icons |
| Kimlik doğrulama | Oturum tabanlı (HttpOnly çerez) |
| Parola özeti | PBKDF2-SHA256 (Django varsayılanı) |

## Kurulum

```bash
# 1) Sanal ortamı etkinleştir
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux/Mac

# 2) Bağımlılıklar (venv içinde kuruludur): Django 6.0, tzdata
#    Gerekirse: pip install Django tzdata

# 3) Veritabanını hazırla
python manage.py migrate

# 4) (İsteğe bağlı) Örnek/demo verisini yükle
python manage.py demo_veri

# 5) (İsteğe bağlı) Yönetici (superuser) oluştur — admin paneli ve tüm yetkiler için
python manage.py createsuperuser

# 6) Sunucuyu başlat
python manage.py runserver
```

Tarayıcı: **http://127.0.0.1:8000/giris/**

`demo_veri` komutu şu hesapları oluşturur: `lider`, `mudur2` (Departman Müdürü),
`talepeden` (Talep Eden), `personel1`, `personel2` (Personel).

Parola kaynak kodda tutulmaz. Komut rastgele bir parola üretip çıktıda bir kez
gösterir; isterseniz kendiniz belirleyebilirsiniz:

```bash
python manage.py demo_veri --parola <seçtiğiniz-parola>
```

Gizli anahtar da kodda yer almaz: geliştirmede ilk çalıştırmada rastgele üretilip
sürüm kontrolü dışındaki `.gizli_anahtar` dosyasına yazılır; üretimde
`DJANGO_SECRET_KEY` ortam değişkeni zorunludur (bkz. `.env.example`).

## Roller ve Yetki Matrisi

| İşlem | Talep Eden | Departman Müdürü | Personel |
|---|---|---|---|
| Talep oluşturma | Evet | Hayır | Hayır |
| Görebildiği talepler | Kendi açtıkları | Kendi departmanının | Kendisine atananlar |
| Gelen talepleri atama / gerekçeyle reddetme | Hayır | Evet | Hayır |
| Talebi aşamalarda ilerletme | Hayır | Evet | Evet (kendisine atananı) |
| Talebi tamamlama (onay) | Hayır | Evet | Hayır |
| Talep arşivleme (yumuşak silme) | Hayır | Evet | Hayır |
| Denetim kayıtları | Hayır | Evet | Hayır |
| Talep içi yorum | Görebildiği talepte | Görebildiği talepte | Görebildiği talepte |

## Testler

```bash
python manage.py test
```

24 test; IDOR/sahiplik denetimi ve departmanlar arası izolasyon, rol denetimi, otomatik
yönlendirme, atama, gerekçeli reddetme, kurallı durum geçişi, hesap kilitleme, denetim
kaydının değiştirilemezliği, yumuşak silme, XSS kaçışı ve parola saklama senaryolarını kapsar.

## Güvenlik Notları (üretim)

- `DJANGO_SECRET_KEY` ortam değişkenini ayarlayın (`.env.example` dosyasına bakın).
- `DJANGO_DEBUG=0` ile hata ayıklama kipini kapatın; bu durumda `Secure` çerezler,
  HTTPS yönlendirmesi ve HSTS otomatik etkinleşir (`config/settings.py`).
- Veritabanı dosyası ve `.env` sürüm kontrolüne dâhil değildir (`.gitignore`).

## Proje Yapısı

```
config/         Ayarlar, kök URL yapılandırması
hesaplar/       Kimlik doğrulama, hesap kilitleme, rol kontrolü (yetkiler.py)
gorevler/       Talep/yorum/bildirim/denetim modelleri ve görünümleri
  loglama.py    Denetim günlüğü yardımcıları
  context_processors.py   Bildirim sayacını her sayfaya taşır
templates/      Bootstrap 5 arayüz şablonları
```
