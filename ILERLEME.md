# Nexa Tweak – İlerleme Notu

Son güncelleme: 08.11.2026

## Tamamlananlar
- Logo: N harfi `assets/logo.png` ve `assets/icon.ico` (arayüz, exe ikonu, .lnk)
- `lic.py`: Ed25519 imzalı lisans. Key = paket (V1/V2/V3) + HWID kilidi + süre + benzersiz id. Exe içinde sadece açık anahtar var.
- `tweaks.py`: V1 (27 özellik, Fivex_V1 zip'inden), V2 (12 özellik + oyun profilleri), V3 (22 özellik + oyun profilleri + sistem taraması/BIOS kontrolü) tek motorda.
- V1'de düzeltilenler: Windows 11'de kalkan `wmic` yerine PowerShell, DoH komutu `doh=yes`, 64-bit kayıt defteri erişimi, diski C: yerine sistem sürücüsü
- `app.py`: tek exe. Lisans ekranı 3. fotoğraftaki tasarım (Beni hatırla, Giriş yap, Anahtar satın al, Destek). Müşteri menüsü, GPU önerileri, BIOS rehberi, admin menü.
- `EXE_OLUSTUR.bat`: py başlatıcısını dener, paketleri kurar, admin anahtarı üretir, tek exe derler, Nexa_Admin ve Nexa_Musteri klasörlerini ve .lnk kısayollarını oluşturur.
- Düzeltilen hata: gen_keys.py ilk çalıştırmada public_key.py yok diye çöküyordu (anahtar ve exe hiç oluşmuyordu).

## 07.11.2026 02:40 güncellemesi
- Tema tamamen lisans ekranındaki gibi: siyah, koyu gri kartlar, beyaz butonlar, kırmızı yok
- Anahtar satın al ve Destek: https://discord.gg/JpVa9ddy5v
- Admin bağlantısı kaldırıldı. nexa_admin.key exe ile aynı klasördeyse exe doğrudan admin şifre ekranıyla açılır, giriş sonrası admin menü gelir. Müşteri klasöründe key yok, normal lisans ekranı açılır.
- Kopyala/yapıştır: Tk panosu yerine Windows pano API'si (clip.py). Ctrl+V, Ctrl+C, Ctrl+A ve sağ tık menüsü çalışır.

## 07.11.2026 12:30 güncellemesi
- Lisans artık SUNUCU tabanlı (Cloudflare Worker, sunucu/ klasörü). Key formatı NEXA-XXXX-XXXX-XXXX-XXXX (karışık harf+rakam).
- Key'i admin panelinden silince müşteri 1-2 dk içinde atılır (exe her 60 sn sunucuya sorar). Müşteri key girince ilk kullandığı bilgisayara kilitlenir (tek kullanımlık). HWID sıfırlama admin panelinde.
- Süre, müşteri keyi ilk kullandığında başlar. Admin, HWID istemeden key üretir.
- Admin exe: Nexa_Admin klasöründe admin.flag var, şifre = sunucuda ADMIN_TOKEN olarak belirlenen şifre. nexa_admin.key ve Ed25519 sistemi kaldırıldı.
- Tweak başlayınca TAM EKRAN kilitli ekran: kapatılamaz (Alt+F4, X, Esc engelli, hep üstte), adım listesi ve yüzde gösterir. Yeniden başlatma başarısız olursa 20 sn sonra kilit açılır.

## 08.11.2026 – V4 + Nexa UI (NUI)
- Yeni paket V4 (38 özellik, 7 oyun profili). V4 anahtarı V1-V4'ün hepsini açar (menüde V1/V2/V3/V4 geçiş düğmesi). Eski V1-V3 anahtarları aynen çalışır.
- `v4.py`: V4 motoru (güç, CPU/arka plan, gecikme, grafik, bellek, disk, temizlik, görünüm, FiveM ayarları, BIOS raporu, Win10/Win11 ayrı ayarlar). `tweaks.py` sonunda otomatik kayıt olur.
- `nui.py`: Nexa UI (tema, bileşenler, pano). `app.py` bundan beslenir.
- Her adım sonucu loglanır (`%APPDATA%\Nexa\last_run.log`), bitişte doğrulama satırları ("Etkin: ..."). Her özellik menüde tek tek kapatılabilir.
- Hızlı Temizlik düğmesi: yeniden başlatmadan arka plan kapatma + önbellek temizliği + RAM boşaltma.
- `sunucu/worker.js` ve `lic.py` V4 kabul eder. **Worker'ı yeniden yayınla:** `npx wrangler deploy` (sunucu klasöründe).
- Linux'ta sahte kayıt defteriyle motor taşıma testi yapıldı (isim hatası yok). Gerçek Windows'ta çalıştırılamadı.

## Sıradaki adımlar (devam için)
1. Windows'ta EXE_OLUSTUR.bat çıktısını dene, hata/ekran görüntüsü paylaş
2. `last_run.log` içindeki "HATA" satırlarına göre düzeltme
3. Fikirler: oyun açılınca otomatik boost (arka plan hizmeti), geri alma (undo) düğmesi, NVIDIA Profile Inspector entegrasyonu

## Bekleyen
- SERVER_URL boş: sunucu/KURULUM.md adımları yapılıp config.py'ye yazılmalı, yoksa EXE_OLUSTUR.bat durur.
- Arayüz ve exe bu ortamda çalıştırılamadı (tkinter/customtkinter/PyInstaller yok). Windows'ta derleyip ekran görüntüsü ile geri bildirim verin.

## Güvenlik uyarısı
Eski repolardaki private.pem, lic_secret.key ve lic_core.py içindeki SECRET herkese açık. Repoları private yapın veya silin.

## Kaldığımız yerden devam
1. sunucu/KURULUM.md adımlarını yap
2. Windows'ta EXE_OLUSTUR.bat çıktısını test et, hataları düzelt
