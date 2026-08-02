# SİYS — Sunum Planı

Staj projesi sunumu için akış ve konuşma notları.

## 1. Problem

Kurumsal yazılım biriminde iç birimlerden (Tahsilat, İK, Muhasebe…) gelen talepler
e-posta, sözlü iletişim ve elektronik tablolarla takip ediliyor. Sonuç: talebin
sorumlusu ve durumu belirsiz, değişiklikler kayıt altında değil, herkes her veriye
erişebiliyor.

## 2. Çözüm

Talepleri merkezî, rol bazlı ve denetlenebilir biçimde yöneten web tabanlı bir sistem:
talep oluştur → personele ata → kurallı durum akışıyla ilerlet → lider onaylasın →
her adım denetim günlüğüne yazılsın.

## 3. Mimarî (tek cümle)

Django (tek sunucu, sunucu tarafı şablon) + SQLite + Bootstrap 5. İki uygulama:
`hesaplar` (kimlik/yetki) ve `gorevler` (talep/yorum/bildirim/denetim).

## 4. Öne çıkan güvenlik unsurları

- **İki katmanlı yetki:** rol (dikey) + kayıt sahipliği / IDOR (yatay).
- **Kurallı durum akışı:** geçersiz geçişler sunucuda reddedilir; onay yalnızca lider.
- **Değiştirilemez denetim günlüğü:** kayıtlar güncellenemez/silinemez.
- **Yumuşak silme:** kayıt bütünlüğü korunur.
- **Hesap kilitleme:** kaba kuvvet denemesine karşı 5/15dk.

## 5. Demo senaryosu (canlı akış)

1. `personel1` ile giriş → yalnızca kendi taleplerini görür (yatay yetki).
2. Adres çubuğunda başkasının talep ID'sini dene → **erişim reddedilir** (IDOR koruması).
3. `lider` ile giriş → tüm talepler + "Yeni Talep" oluştur, `personel2`'ye ata.
4. Kanban panosunda talebi durumlar arasında ilerlet; geçersiz geçişi dene → reddedilir.
5. `personel2` ile talebi "Testte"ye getir; "Tamamla" butonu **görünmez** (yalnızca lider).
6. `lider` talebi tamamlar (onay).
7. Talebi arşivle → listeden çıkar ama veritabanında durur (yumuşak silme).
8. Denetim günlüğünü aç → tüm işlemler kim/ne zaman/hangi IP ile kayıtlı.
9. 5 kez hatalı giriş → hesap 15 dk kilitlenir.

## 6. Kalite

`python manage.py test` → 16 test (IDOR, rol, durum geçişi, kilitleme, denetim,
soft delete, XSS, parola saklama) yeşil.

## 7. Bilinen eksikler ve gelecek geliştirmeler

- E-posta bildirimi (şu an yalnızca uygulama içi).
- Dosya ekleme modülü.
- Takvim görünümü ve tekrarlayan talep üretimi.
- Üretim yapılandırması: PostgreSQL, HTTPS, uygulama sunucusu.
- Kanban'da sürükle-bırak.

## 8. Öğrenilenler

Django istek-yanıt döngüsü, ORM ile ilişkisel modelleme, oturum tabanlı kimlik
doğrulama, rol ve kayıt bazlı yetkilendirme, yaygın web açıklarının (IDOR, XSS, CSRF,
SQL enjeksiyonu) nedenleri ve çözümleri, otomatik test yazımı ve kısıtlı sürede
kapsam önceliklendirme.
