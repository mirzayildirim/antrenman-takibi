# Antrenman Takibi

Flet tabanlı web uygulaması. Veriler Google Apps Script üzerinden Google Sheets'te saklanır.

## Güvenlik

- `ANTRENMAN_API_URL` ve `ANTRENMAN_API_TOKEN` yalnızca hosting sağlayıcısının Environment/Secrets ayarlarına girilmelidir.
- Gerçek token, `.env` dosyası, kullanıcı verileri veya `antrenman_verileri.json` GitHub'a yüklenmemelidir.
- Google Apps Script'teki tek hücreli JSON depolaması küçük ölçekli deneme içindir; Apps Script kodu 45.000 karakter sınırı uygular.

## Çalıştırma

Python 3.11 ile:

```bash
pip install -r requirements.txt
flet run --web --host 0.0.0.0 --port 8550 main.py
```

Hosting ortamında `ANTRENMAN_API_URL` ve `ANTRENMAN_API_TOKEN` değişkenlerini tanımlayın.

## Varlıklar

Uygulama `assets/PullUP.webp` dosyasını kullanır. Bu dosya ve gerekiyorsa profil fotoğrafları uygulama paketiyle ayrıca sağlanmalıdır.
