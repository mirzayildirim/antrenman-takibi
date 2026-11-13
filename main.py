import flet as ft
import json
import os
import hashlib
import secrets
import urllib.parse
import urllib.request
from datetime import datetime

# --- GOOGLE SHEETS BULUT VERİTABANI ---
# API adresi ve anahtarı yalnızca hosting ortam değişkenlerinde tanımlanır.
# Bu değerleri GitHub'a veya kaynak dosyaya kesinlikle eklemeyin.
API_URL = os.environ.get("ANTRENMAN_API_URL", "")
API_TOKEN = os.environ.get("ANTRENMAN_API_TOKEN", "")


def _api_kontrol_():
    if not API_TOKEN:
        raise RuntimeError(
            "ANTRENMAN_API_TOKEN tanımlı değil. Google API anahtarını sunucu ortam değişkenine ekleyin."
        )
    if not API_URL:
        raise RuntimeError("ANTRENMAN_API_URL tanımlı değil.")


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 310000)
    return salt.hex() + "$" + digest.hex()


def verify_password(user_data, password):
    stored = user_data.get("sifre_hash")
    if stored:
        try:
            salt_hex, digest_hex = stored.split("$", 1)
            digest = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 310000
            )
            return secrets.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError):
            return False
    # Eski sürümden kalan hesap varsa, başarılı girişte hash'e yükselt.
    return user_data.get("sifre") == password


def load_data():
    _api_kontrol_()
    query = urllib.parse.urlencode({"action": "load", "token": API_TOKEN})
    request = urllib.request.Request(f"{API_URL}?{query}", method="GET")
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Google verileri okunamadı."))
    data = result.get("data", {})
    if not isinstance(data, dict):
        raise RuntimeError("Google veritabanından beklenmeyen veri geldi.")
    return data


def save_data(data):
    _api_kontrol_()
    payload = json.dumps(
        {"action": "save", "token": API_TOKEN, "data": data},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("ok") or not result.get("saved"):
        raise RuntimeError(result.get("error", "Google verileri kaydedemedi."))


def main(page: ft.Page):
    # --- SAYFA AYARLARI ---
    page.title = "Antrenman Takibi"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 400
    page.window.height = 800
    page.padding = 0  
    page.bgcolor = ft.Colors.BLACK  
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.CYAN) 

    durum = {
        "aktif_kullanici": None, 
        "secili_tarih": "",
        "aktif_egzersizler": [],
        "set_kutulari": [],
        "duzenlenen_index": None
    }

    profil_dosya_secici = ft.FilePicker()
    page.overlay.append(profil_dosya_secici)

    katalog = {
        "Bench Press": "Chest", "Incline Dumbbell Press": "Chest",
        "Pull Up": "Back", "Barbell Row": "Back",
        "Shoulder Press": "Shoulders", "Lateral Raise": "Shoulders",
        "Squat": "Quadriceps", "Leg Extension": "Quadriceps",
        "Romanian Deadlift": "Hamstrings", "Leg Curl": "Hamstrings",
        "Bicep Curl": "Biceps", "Hammer Curl": "Biceps",
        "Tricep Extension": "Triceps", "Crunch": "Abs", "Calf Raise": "Calves"
    }

    # Profil fotoğrafları assets/profil_fotograflari klasöründe saklanır.
    def profil_avatar_olustur(kullanici_adi, boyut=44):
        kullanici_verisi = load_data().get(kullanici_adi, {})
        foto_yolu = kullanici_verisi.get("profil_fotografi")
        if foto_yolu and os.path.isfile(os.path.join("assets", foto_yolu)):
            avatar_icerik = ft.Image(
                src=foto_yolu,
                width=boyut,
                height=boyut,
                fit=ft.BoxFit.COVER,
            )
        else:
            avatar_icerik = ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=boyut * 0.55)
        return ft.CircleAvatar(
            radius=boyut / 2,
            bgcolor=ft.Colors.GREY_700,
            content=avatar_icerik,
        )

    def tab_degisti(e):
        index = e.control.selected_index
        if index == 0: ana_ekrani_goster()
        elif index == 1: gecmis_ekrani_goster()
        elif index == 2: analiz_ekrani_goster()
        elif index == 3: sosyal_ekrani_goster()
        elif index == 4: profil_ekrani_goster()

    gezinme_cubugu = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER, label="İdman"),
            ft.NavigationBarDestination(icon=ft.Icons.HISTORY, label="Geçmiş"),
            ft.NavigationBarDestination(icon=ft.Icons.INSERT_CHART_OUTLINED, label="Analiz"),
            ft.NavigationBarDestination(icon=ft.Icons.PEOPLE, label="Sosyal"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profil"),
        ],
        bgcolor=ft.Colors.GREY_900,
        selected_index=0,
        on_change=tab_degisti
    )

    # ==========================================
    # 0. PENCERE: GİRİŞ & KAYIT OL EKRANLARI
    # ==========================================
    login_kadi = ft.TextField(label="Kullanıcı Adı", width=320, border_color=ft.Colors.CYAN_700, border_radius=10)
    login_sifre = ft.TextField(label="Şifre", width=320, border_color=ft.Colors.CYAN_700, border_radius=10, password=True, can_reveal_password=True)
    
    kayit_ad = ft.TextField(label="İsim", width=320, border_color=ft.Colors.CYAN_700, border_radius=10)
    kayit_soyad = ft.TextField(label="Soyisim", width=320, border_color=ft.Colors.CYAN_700, border_radius=10)
    kayit_kadi = ft.TextField(label="Kullanıcı Adı (Benzersiz)", width=320, border_color=ft.Colors.CYAN_700, border_radius=10)
    kayit_sifre = ft.TextField(label="Şifre", width=320, border_color=ft.Colors.CYAN_700, border_radius=10, password=True, can_reveal_password=True)

    def giris_yap_tetikle(e):
        k = login_kadi.value.strip().lower()
        s = login_sifre.value.strip()
        veri = load_data()
        
        if k in veri and verify_password(veri[k], s):
            if "sifre_hash" not in veri[k]:
                veri[k]["sifre_hash"] = hash_password(s)
                veri[k].pop("sifre", None)
                save_data(veri)
            durum["aktif_kullanici"] = k
            page.navigation_bar = gezinme_cubugu 
            ana_ekrani_goster()
        else:
            page.overlay.append(ft.SnackBar(ft.Text("Kullanıcı adı veya şifre hatalı!"), bgcolor=ft.Colors.RED_700, open=True))
            page.update()

    def kayit_ol_tetikle(e):
        k = kayit_kadi.value.strip().lower()
        if not k or not kayit_ad.value or not kayit_sifre.value:
            page.overlay.append(ft.SnackBar(ft.Text("Lütfen tüm alanları doldurun!"), bgcolor=ft.Colors.RED_700, open=True))
            page.update()
            return
        if len(kayit_sifre.value.strip()) < 8:
            page.overlay.append(ft.SnackBar(ft.Text("Şifre en az 8 karakter olmalı."), bgcolor=ft.Colors.RED_700, open=True))
            page.update()
            return
        veri = load_data()
        if k in veri:
            page.overlay.append(ft.SnackBar(ft.Text("Bu kullanıcı adı zaten alınmış!"), bgcolor=ft.Colors.RED_700, open=True))
            page.update()
            return
        veri[k] = {"sifre_hash": hash_password(kayit_sifre.value.strip()), "ad": kayit_ad.value.strip(), "soyad": kayit_soyad.value.strip(), "antrenmanlar": [], "arkadaslar": [], "gelen_istekler": [], "puan": 0}
        save_data(veri)
        page.overlay.append(ft.SnackBar(ft.Text("Kayıt başarılı! Şimdi giriş yapabilirsiniz."), bgcolor=ft.Colors.GREEN_700, open=True))
        login_ekrani_goster()

    def kayit_ekranina_gec(e):
        kayit_ad.value = ""; kayit_soyad.value = ""; kayit_kadi.value = ""; kayit_sifre.value = ""
        page.controls.clear()
        icerik = ft.Column([
            ft.Container(height=40), ft.Icon(ft.Icons.PERSON_ADD, size=60, color=ft.Colors.CYAN_ACCENT),
            ft.Text("Kayıt Ol", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(height=20),
            kayit_ad, kayit_soyad, kayit_kadi, kayit_sifre, ft.Container(height=10),
            ft.Button("Hesap Oluştur", on_click=kayit_ol_tetikle, width=320, height=55, style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))),
            ft.TextButton("Zaten hesabın var mı? Giriş Yap", on_click=lambda e: login_ekrani_goster())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        page.add(ft.Container(content=icerik, padding=20, expand=True))
        page.update()

    def login_ekrani_goster():
        page.navigation_bar = None
        login_kadi.value = ""; login_sifre.value = "" 
        page.controls.clear()
        icerik = ft.Column([
            ft.Container(height=80), ft.Icon(ft.Icons.LOCK_PERSON, size=80, color=ft.Colors.CYAN_ACCENT),
            ft.Text("Giriş Yap", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(height=40),
            login_kadi, login_sifre, ft.Container(height=20),
            ft.Button("Giriş", on_click=giris_yap_tetikle, width=320, height=55, style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))),
            ft.TextButton("Hesabın yok mu? Kayıt Ol", on_click=kayit_ekranina_gec)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        page.add(ft.Container(content=icerik, padding=20, expand=True))
        page.update()

    # ==========================================
    # 1. PENCERE: ANA EKRAN (YENİ ANTRENMAN)
    # ==========================================
    tarih_input = ft.TextField(value=datetime.today().strftime("%Y-%m-%d"), width=320, border_color=ft.Colors.CYAN_700, border_radius=10, text_align=ft.TextAlign.CENTER)

    def antrenmana_basla_tiklandi(e):
        durum["secili_tarih"] = tarih_input.value
        durum["duzenlenen_index"] = None 
        durum["aktif_egzersizler"].clear()
        durum["set_kutulari"].clear()
        
        # Yeni oturum ekranını yeniden inşa et ve yükle
        yenile_antrenman_ekrani()

    def ana_ekrani_goster():
        veri = load_data()
        isim = veri[durum["aktif_kullanici"]].get("ad", "")
        ana_ekran_icerik = ft.Column([
            ft.Container(height=60), ft.Icon(ft.Icons.FITNESS_CENTER, size=80, color=ft.Colors.CYAN_ACCENT),
            ft.Text(f"Hoş geldin, {isim}!", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT_100),
            ft.Text("Antrenman Takibi", size=30, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(height=40),
            tarih_input, ft.Container(height=20),
            ft.Button("🚀 Yeni Antrenman Başlat", on_click=antrenmana_basla_tiklandi, width=320, height=60, style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=15))),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        page.controls.clear()
        page.navigation_bar.selected_index = 0
        page.add(ft.Container(content=ana_ekran_icerik, padding=20, expand=True))
        page.update()

    # ==========================================
    # 2. PENCERE: AKTİF ANTRENMAN EKRANI BİLEŞENLERİ
    # ==========================================
    oturumdaki_hareketler_arayuzu = ft.Column(spacing=10)
    set_listesi_arayuzu = ft.Column(spacing=10)
    
    # Global referanslar
    hareket_dropdown = ft.Dropdown(width=320, border_color=ft.Colors.CYAN_ACCENT_700, border_radius=10, filled=True, fill_color=ft.Colors.BLACK)
    gorsel_kutusu = ft.Container(width=320, height=180, border_radius=15, bgcolor=ft.Colors.GREY_900, alignment=ft.alignment.Alignment(0, 0))
    arama_kutusu = ft.TextField(hint_text="Egzersiz ara...", width=160, border_color=ft.Colors.CYAN_700, border_radius=10, content_padding=10, prefix_icon=ft.Icons.SEARCH)
    kas_gruplari = ["All muscles"] + sorted(list(set(katalog.values())))
    kas_grubu_filtre = ft.Dropdown(options=[ft.dropdown.Option(m) for m in kas_gruplari], value="All muscles", width=150, border_color=ft.Colors.CYAN_700, border_radius=10, content_padding=10)

    def hareket_degisti(e):
        secilen = hareket_dropdown.value
        secilen_temiz = secilen.strip().lower() if secilen else ""
        
        gorsel_kutusu.content = None
        
        if "pull up" in secilen_temiz:
            gorsel_kutusu.content = ft.Image(src="PullUP.webp", width=320, height=180, fit=ft.BoxFit.CONTAIN)
        else:
            isim = secilen if secilen else "Hareket Bulunamadı"
            gorsel_kutusu.content = ft.Text(isim, size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT, text_align=ft.TextAlign.CENTER)
            
        page.update()

    hareket_dropdown.on_select = hareket_degisti

    def filtrele(e):
        arama = arama_kutusu.value.lower() if arama_kutusu.value else ""
        kas = kas_grubu_filtre.value if kas_grubu_filtre.value else "All muscles"
        
        filtrelenmis = [h for h, k in katalog.items() if (kas == "All muscles" or k == kas) and (not arama or arama in h.lower())]
        hareket_dropdown.options = [ft.dropdown.Option(x) for x in filtrelenmis]
        
        if filtrelenmis:
            hareket_dropdown.value = filtrelenmis[0]
            secilen_temiz = filtrelenmis[0].strip().lower()
            if "pull up" in secilen_temiz:
                gorsel_kutusu.content = ft.Image(src="PullUP.webp", width=320, height=180, fit=ft.BoxFit.CONTAIN)
            else:
                gorsel_kutusu.content = ft.Text(filtrelenmis[0], size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT, text_align=ft.TextAlign.CENTER)
        else:
            hareket_dropdown.value = None
            gorsel_kutusu.content = ft.Text("Hareket Bulunamadı", size=20, color=ft.Colors.RED_400)
            
        page.update()

    arama_kutusu.on_change = filtrele
    kas_grubu_filtre.on_change = filtrele

    def oturum_arayuzunu_guncelle():
        oturumdaki_hareketler_arayuzu.controls.clear()
        if durum["aktif_egzersizler"]:
            oturumdaki_hareketler_arayuzu.controls.append(ft.Text("Şu Ana Kadar Eklenenler:", weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT, size=18))
            for i, egzersiz in enumerate(durum["aktif_egzersizler"]):
                set_metinleri = []
                for s in egzersiz["setler"]:
                    set_metinleri.append(ft.Text(f"Set {s['set']}: {s['agirlik']} kg x {s['tekrar']} tekrar", color=ft.Colors.GREY_400, size=14))
                
                def hareketi_oturumdan_sil(e):
                    silinecek_idx = e.control.data
                    durum["aktif_egzersizler"].pop(silinecek_idx)
                    oturum_arayuzunu_guncelle()
                    page.update()
                
                kart = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(egzersiz["hareket"], weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=16),
                                ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, data=i, on_click=hareketi_oturumdan_sil)
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            *set_metinleri
                        ], spacing=5),
                        padding=15, bgcolor=ft.Colors.GREY_800, border_radius=10
                    ), elevation=2
                )
                oturumdaki_hareketler_arayuzu.controls.append(kart)

    def set_ekle(e):
        set_no = len(durum["set_kutulari"]) + 1
        tekrar_txt = ft.Text("10", size=20, weight=ft.FontWeight.BOLD, width=35, text_align=ft.TextAlign.CENTER)
        agirlik_txt = ft.Text("20", size=20, weight=ft.FontWeight.BOLD, width=50, text_align=ft.TextAlign.CENTER)

        def eksi_tekrar(e):
            v = int(tekrar_txt.value); 
            if v > 0: tekrar_txt.value = str(v - 1); tekrar_txt.update()
        def arti_tekrar(e):
            tekrar_txt.value = str(int(tekrar_txt.value) + 1); tekrar_txt.update()
        def eksi_agirlik(e):
            v = float(agirlik_txt.value)
            if v > 0: yeni = v - 2.5; agirlik_txt.value = str(int(yeni) if yeni.is_integer() else yeni); agirlik_txt.update()
        def arti_agirlik(e):
            v = float(agirlik_txt.value); yeni = v + 2.5; agirlik_txt.value = str(int(yeni) if yeni.is_integer() else yeni); agirlik_txt.update()

        satir_icerigi = ft.Container(
            content=ft.Row([
                ft.Container(ft.Text(f"Set {set_no}", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT), width=50),
                ft.Row([ft.IconButton(ft.Icons.REMOVE_CIRCLE, on_click=eksi_tekrar, icon_color=ft.Colors.RED_400, icon_size=24), tekrar_txt, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=arti_tekrar, icon_color=ft.Colors.GREEN_400, icon_size=24)], spacing=0),
                ft.Row([ft.IconButton(ft.Icons.REMOVE_CIRCLE, on_click=eksi_agirlik, icon_color=ft.Colors.RED_400, icon_size=24), agirlik_txt, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=arti_agirlik, icon_color=ft.Colors.GREEN_400, icon_size=24)], spacing=0),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=10, bgcolor=ft.Colors.GREY_900, border_radius=12
        )
        durum["set_kutulari"].append({"tekrar": tekrar_txt, "agirlik": agirlik_txt})
        set_listesi_arayuzu.controls.append(satir_icerigi)
        page.update()

    def egzersizi_kaydet(e):
        if not durum["set_kutulari"]:
            page.overlay.append(ft.SnackBar(ft.Text("Lütfen en az 1 set ekleyin!"), bgcolor=ft.Colors.RED_700, open=True))
            page.update()
            return
        yeni_hareket = {
            "hareket": hareket_dropdown.value,
            "setler": [{"set": i+1, "tekrar": s["tekrar"].value, "agirlik": s["agirlik"].value} for i, s in enumerate(durum["set_kutulari"])]
        }
        durum["aktif_egzersizler"].append(yeni_hareket)
        durum["set_kutulari"].clear()
        set_listesi_arayuzu.controls.clear()
        oturum_arayuzunu_guncelle()
        
        if e is not None: 
            page.overlay.append(ft.SnackBar(ft.Text(f"✅ {hareket_dropdown.value} oturuma eklendi!"), bgcolor=ft.Colors.GREEN_700, open=True))
        page.update()

    def antrenmani_bitir(e):
        if durum["set_kutulari"]:
            egzersizi_kaydet(None)

        if not durum["aktif_egzersizler"]:
            page.overlay.append(ft.SnackBar(ft.Text("Antrenmana hiç hareket eklemediniz!"), bgcolor=ft.Colors.RED_700, open=True))
            page.update()
            return
            
        veri = load_data()
        yeni_kayit = {"tarih": durum["secili_tarih"], "egzersizler": durum["aktif_egzersizler"].copy()}
        
        if durum["duzenlenen_index"] is not None:
            veri[durum["aktif_kullanici"]]["antrenmanlar"][durum["duzenlenen_index"]] = yeni_kayit
            durum["duzenlenen_index"] = None
            mesaj = "🎉 Antrenman başarıyla güncellendi!"
        else:
            veri[durum["aktif_kullanici"]]["antrenmanlar"].append(yeni_kayit)
            mesaj = "🎉 Antrenman başarıyla kaydedildi!"
            
        save_data(veri)
        durum["aktif_egzersizler"].clear()
        durum["set_kutulari"].clear()
        set_listesi_arayuzu.controls.clear()
        oturum_arayuzunu_guncelle()
        
        page.overlay.append(ft.SnackBar(ft.Text(mesaj), bgcolor=ft.Colors.CYAN_700, open=True))
        ana_ekrani_goster()

    def yenile_antrenman_ekrani():
        oturum_arayuzunu_guncelle()
        set_listesi_arayuzu.controls.clear()
        arama_kutusu.value = ""
        kas_grubu_filtre.value = "All muscles"
        filtrele(None)

        filtre_satiri = ft.Row([arama_kutusu, kas_grubu_filtre], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=320)
        ust_kart = ft.Card(content=ft.Container(content=ft.Column([ft.Text("Yeni Egzersiz Ekle", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_ACCENT), filtre_satiri, hareket_dropdown, gorsel_kutusu], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15), padding=20, bgcolor=ft.Colors.GREY_900, border_radius=15), elevation=10, margin=20)

        antrenman_ekrani_icerik = ft.ListView(
            controls=[
                ft.Container(content=ft.Text("Aktif Antrenman", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), padding=20),
                ft.Container(content=oturumdaki_hareketler_arayuzu, padding=20), 
                ust_kart, 
                ft.Container(content=set_listesi_arayuzu, padding=20),
                ft.Container(content=ft.Button("➕ Set Ekle", on_click=set_ekle, width=320, height=50, style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_800, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))), padding=10),
                ft.Container(content=ft.Button("💾 Hareketi Antrenmana Ekle", on_click=egzersizi_kaydet, width=320, height=55, style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))), padding=10),
                ft.Container(content=ft.Button("🔴 Tüm Antrenmanı Bitir", on_click=antrenmani_bitir, width=320, height=55, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))), padding=20)
            ], expand=True
        )

        page.controls.clear()
        page.add(antrenman_ekrani_icerik)
        page.update()

    # ==========================================
    # 3. PENCERE: GEÇMİŞ EKRANI
    # ==========================================
    def antrenman_sil(e):
        silinecek_index = e.control.data
        veri = load_data()
        veri[durum["aktif_kullanici"]]["antrenmanlar"].pop(silinecek_index)
        save_data(veri)
        page.overlay.append(ft.SnackBar(ft.Text("🗑️ Antrenman silindi!"), bgcolor=ft.Colors.RED_700, open=True))
        gecmis_ekrani_goster()

    def antrenman_duzenle(e):
        duzenlenecek_index = e.control.data
        veri = load_data()
        secilen_antrenman = veri[durum["aktif_kullanici"]]["antrenmanlar"][duzenlenecek_index]
        durum["secili_tarih"] = secilen_antrenman["tarih"]
        durum["aktif_egzersizler"] = secilen_antrenman["egzersizler"].copy()
        durum["duzenlenen_index"] = duzenlenecek_index
        
        yenile_antrenman_ekrani()
        page.overlay.append(ft.SnackBar(ft.Text("✏️ Düzenleme Modu aktif."), bgcolor=ft.Colors.ORANGE_700, open=True))

    def gecmis_ekrani_goster():
        page.controls.clear()
        page.navigation_bar.selected_index = 1
        veri = load_data()
        kullanici_antrenmanlari = veri[durum["aktif_kullanici"]].get("antrenmanlar", [])
        
        for i, k in enumerate(kullanici_antrenmanlari): 
            k["_index"] = i
            
        kullanici_antrenmanlari.sort(key=lambda x: x.get("tarih", ""), reverse=True)
        
        liste = ft.ListView(expand=True, spacing=15, padding=20)
        liste.controls.append(ft.Text("Geçmiş Antrenmanlar", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE))
        
        if not kullanici_antrenmanlari:
            liste.controls.append(ft.Text("Kayıtlı antrenman yok.", color=ft.Colors.GREY_500, size=16))
        else:
            for kayit in kullanici_antrenmanlari:
                tarih = kayit.get("tarih", "Bilinmeyen Tarih")
                egzersizler = kayit.get("egzersizler", [])
                ozet_satirlari = []
                for e in egzersizler:
                    hareket = e.get("hareket", "")
                    set_sayisi = len(e.get("setler", []))
                    toplam_tekrar = sum(int(s.get("tekrar", 0)) for s in e.get("setler", []))
                    ozet_satirlari.append(ft.Text(f"• {hareket} ({set_sayisi} Set, {toplam_tekrar} Tekrar)", color=ft.Colors.CYAN_ACCENT_100, size=14))
                
                baslik_satiri = ft.Row([
                    ft.Text(f"📅 {tarih}", weight=ft.FontWeight.BOLD, size=18, color=ft.Colors.CYAN_400),
                    ft.Row([
                        ft.IconButton(ft.Icons.EDIT, icon_color=ft.Colors.ORANGE_400, data=kayit["_index"], on_click=antrenman_duzenle), 
                        ft.IconButton(ft.Icons.DELETE, icon_color=ft.Colors.RED_400, data=kayit["_index"], on_click=antrenman_sil)
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                
                kart = ft.Card(content=ft.Container(content=ft.Column([baslik_satiri, ft.Divider(color=ft.Colors.GREY_700), *ozet_satirlari], spacing=5), padding=15, bgcolor=ft.Colors.GREY_900, border_radius=10), elevation=5, margin=10)
                liste.controls.append(kart)
                
        page.add(liste)
        page.update()

    # ==========================================
    # 4. PENCERE: ANALİZ EKRANI
    # ==========================================
    def analiz_ekrani_goster():
        page.controls.clear()
        page.navigation_bar.selected_index = 2
        analiz_icerik = ft.Column([
            ft.Container(height=60), ft.Icon(ft.Icons.INSERT_CHART_OUTLINED, size=80, color=ft.Colors.CYAN_ACCENT), 
            ft.Text("Antrenman Analizi", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(height=20), 
            ft.Text("Yakında buraya grafikler gelecek!", text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_400, size=16)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.add(ft.Container(content=analiz_icerik, padding=30, expand=True))
        page.update()

    # ==========================================
    # 5. PENCERE: SOSYAL AĞ EKRANI
    # ==========================================
    def sosyal_ekrani_goster():
        page.controls.clear()
        page.navigation_bar.selected_index = 3
        veri = load_data()
        aktif_kisi_veri = veri[durum["aktif_kullanici"]]
        
        aranan_kadi_input = ft.TextField(hint_text="Kullanıcı Adı Girin", width=200, border_color=ft.Colors.CYAN_700, border_radius=10, content_padding=10)
        
        def istek_gonder(e):
            hedef = aranan_kadi_input.value.strip().lower()
            guncel_veri = load_data()
            if not hedef: return
            if hedef == durum["aktif_kullanici"]:
                page.overlay.append(ft.SnackBar(ft.Text("Kendinize istek atamazsınız!"), bgcolor=ft.Colors.RED_700, open=True)); page.update(); return
            if hedef not in guncel_veri:
                page.overlay.append(ft.SnackBar(ft.Text("Böyle bir kullanıcı bulunamadı!"), bgcolor=ft.Colors.RED_700, open=True)); page.update(); return
            if hedef in guncel_veri[durum["aktif_kullanici"]].get("arkadaslar", []):
                page.overlay.append(ft.SnackBar(ft.Text("Bu kişi zaten listenizde!"), bgcolor=ft.Colors.RED_700, open=True)); page.update(); return
            if durum["aktif_kullanici"] in guncel_veri[hedef].get("gelen_istekler", []):
                page.overlay.append(ft.SnackBar(ft.Text("İstek zaten gönderilmiş!"), bgcolor=ft.Colors.ORANGE_700, open=True)); page.update(); return
                
            guncel_veri[hedef].setdefault("gelen_istekler", []).append(durum["aktif_kullanici"])
            save_data(guncel_veri)
            aranan_kadi_input.value = ""
            page.overlay.append(ft.SnackBar(ft.Text(f"{hedef} kullanıcısına istek gönderildi!"), bgcolor=ft.Colors.GREEN_700, open=True))
            sosyal_ekrani_goster()

        istek_satiri = ft.Row([aranan_kadi_input, ft.IconButton(ft.Icons.SEND, on_click=istek_gonder, icon_color=ft.Colors.CYAN_ACCENT)], alignment=ft.MainAxisAlignment.CENTER)
        
        gelen_istekler_arayuzu = ft.Column(spacing=5)
        gelen_istekler = aktif_kisi_veri.get("gelen_istekler", [])
        
        def istek_kabul_et(e):
            kabul_edilen = e.control.data
            guncel_veri = load_data()
            guncel_veri[durum["aktif_kullanici"]]["gelen_istekler"].remove(kabul_edilen)
            guncel_veri[durum["aktif_kullanici"]].setdefault("arkadaslar", []).append(kabul_edilen)
            guncel_veri[kabul_edilen].setdefault("arkadaslar", []).append(durum["aktif_kullanici"])
            save_data(guncel_veri)
            page.overlay.append(ft.SnackBar(ft.Text(f"{kabul_edilen} ile arkadaş oldunuz!"), bgcolor=ft.Colors.GREEN_700, open=True))
            sosyal_ekrani_goster()

        if gelen_istekler:
            gelen_istekler_arayuzu.controls.append(ft.Text("📥 Gelen İstekler", color=ft.Colors.ORANGE_400, weight=ft.FontWeight.BOLD))
            for kisi in gelen_istekler:
                gelen_istekler_arayuzu.controls.append(
                    ft.Container(content=ft.Row([
                        ft.Row([profil_avatar_olustur(kisi, 38), ft.Text(f"@{kisi}", color=ft.Colors.WHITE, size=16)], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.IconButton(ft.Icons.CHECK_CIRCLE, icon_color=ft.Colors.GREEN_400, data=kisi, on_click=istek_kabul_et)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=10, bgcolor=ft.Colors.GREY_900, border_radius=10)
                )

        liderlik_arayuzu = ft.Column(spacing=10)
        liderlik_arayuzu.controls.append(ft.Text("🏆 Liderlik Tablosu", color=ft.Colors.CYAN_ACCENT, weight=ft.FontWeight.BOLD, size=18))
        
        arkadas_listesi = aktif_kisi_veri.get("arkadaslar", [])
        tablo_kisileri = arkadas_listesi + [durum["aktif_kullanici"]]
        tablo_kisileri.sort(key=lambda x: veri.get(x, {}).get("puan", 0), reverse=True)
        
        for sirada, kisi in enumerate(tablo_kisileri):
            puan = veri.get(kisi, {}).get("puan", 0)
            isim = "Sen" if kisi == durum["aktif_kullanici"] else f"@{kisi}"
            renk = ft.Colors.CYAN_400 if kisi == durum["aktif_kullanici"] else ft.Colors.WHITE
            liderlik_arayuzu.controls.append(ft.Container(content=ft.Row([
                ft.Row([profil_avatar_olustur(kisi, 42), ft.Text(f"{sirada+1}. {isim}", color=renk, weight=ft.FontWeight.BOLD, size=16)], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Text(f"{puan} Puan", color=ft.Colors.YELLOW_600, weight=ft.FontWeight.BOLD, size=16)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), padding=15, bgcolor=ft.Colors.GREY_800, border_radius=10))

        sayfa_icerik = ft.ListView(controls=[ft.Text("Sosyal Ağ", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Divider(height=20, color=ft.Colors.TRANSPARENT), ft.Text("Arkadaş Ekle", size=16, color=ft.Colors.GREY_400), istek_satiri, ft.Divider(height=20, color=ft.Colors.TRANSPARENT), gelen_istekler_arayuzu, ft.Divider(height=20, color=ft.Colors.TRANSPARENT), liderlik_arayuzu], padding=20, expand=True)
        page.add(sayfa_icerik)
        page.update()

    # ==========================================
    # 6. PENCERE: PROFİL EKRANI
    # ==========================================
    def profil_ekrani_goster():
        page.controls.clear()
        page.navigation_bar.selected_index = 4
        veri = load_data()
        
        isim = veri[durum["aktif_kullanici"]].get("ad", "")
        soyisim = veri[durum["aktif_kullanici"]].get("soyad", "")
        kullanici_adi_metni = f"@{durum['aktif_kullanici']}"
        
        isim_input = ft.TextField(label="İsim", value=isim, width=320, border_color=ft.Colors.CYAN_700, border_radius=10, text_align=ft.TextAlign.CENTER)
        soyisim_input = ft.TextField(label="Soyisim", value=soyisim, width=320, border_color=ft.Colors.CYAN_700, border_radius=10, text_align=ft.TextAlign.CENTER)
        yeni_sifre_input = ft.TextField(label="Yeni Şifre", password=True, can_reveal_password=True, width=320, border_color=ft.Colors.CYAN_700, border_radius=10, text_align=ft.TextAlign.CENTER)

        # FilePicker servisi profil fotoğrafı seçmek için kullanılır.
        async def profil_fotografi_sec(e):
            secilen_dosyalar = await profil_dosya_secici.pick_files(
                allow_multiple=False,
                with_data=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
            )
            if not secilen_dosyalar:
                return

            dosya = secilen_dosyalar[0]
            uzanti = os.path.splitext(dosya.name)[1].lower()
            if uzanti not in [".jpg", ".jpeg", ".png", ".webp"]:
                page.overlay.append(ft.SnackBar(ft.Text("Lütfen JPG, JPEG, PNG veya WEBP formatında fotoğraf seçin."), bgcolor=ft.Colors.RED_700, open=True))
                page.update()
                return

            foto_klasoru = os.path.join("assets", "profil_fotograflari")
            os.makedirs(foto_klasoru, exist_ok=True)
            guvenli_kullanici = "".join(c for c in durum["aktif_kullanici"] if c.isalnum() or c in "_-")
            dosya_adi = f"{guvenli_kullanici}{uzanti}"
            tam_yol = os.path.join(foto_klasoru, dosya_adi)

            if dosya.bytes:
                with open(tam_yol, "wb") as foto_dosyasi:
                    foto_dosyasi.write(dosya.bytes)
            elif dosya.path and os.path.isfile(dosya.path):
                import shutil
                shutil.copy2(dosya.path, tam_yol)
            else:
                page.overlay.append(ft.SnackBar(ft.Text("Fotoğraf okunamadı. Lütfen tekrar deneyin."), bgcolor=ft.Colors.RED_700, open=True))
                page.update()
                return

            guncel_veri = load_data()
            guncel_veri[durum["aktif_kullanici"]]["profil_fotografi"] = f"profil_fotograflari/{dosya_adi}"
            save_data(guncel_veri)
            page.overlay.append(ft.SnackBar(ft.Text("✅ Profil fotoğrafınız güncellendi!"), bgcolor=ft.Colors.GREEN_700, open=True))
            profil_ekrani_goster()

        def profili_kaydet(e):
            guncel_veri = load_data()
            guncel_veri[durum["aktif_kullanici"]]["ad"] = isim_input.value
            guncel_veri[durum["aktif_kullanici"]]["soyad"] = soyisim_input.value
            
            if yeni_sifre_input.value.strip():
                if len(yeni_sifre_input.value.strip()) < 8:
                    page.overlay.append(ft.SnackBar(ft.Text("Yeni şifre en az 8 karakter olmalı."), bgcolor=ft.Colors.RED_700, open=True))
                    page.update()
                    return
                guncel_veri[durum["aktif_kullanici"]]["sifre_hash"] = hash_password(yeni_sifre_input.value.strip())
                guncel_veri[durum["aktif_kullanici"]].pop("sifre", None)
                
            save_data(guncel_veri)
            yeni_sifre_input.value = "" 
            page.overlay.append(ft.SnackBar(ft.Text("✅ Profil başarıyla güncellendi!"), bgcolor=ft.Colors.GREEN_700, open=True))
            page.update()
            
        def cikis_yap(e):
            durum["aktif_kullanici"] = None
            login_ekrani_goster()

        profil_icerik = ft.Column([
            ft.Container(height=30), ft.Text("Profilim", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Container(height=10),
            ft.Text(kullanici_adi_metni, color=ft.Colors.CYAN_ACCENT, size=18, weight=ft.FontWeight.BOLD), ft.Container(height=20),
            ft.CircleAvatar(radius=60, bgcolor=ft.Colors.GREY_800, content=(
                ft.Image(src=veri[durum["aktif_kullanici"]]["profil_fotografi"], width=120, height=120, fit=ft.BoxFit.COVER)
                if veri[durum["aktif_kullanici"]].get("profil_fotografi") and os.path.isfile(os.path.join("assets", veri[durum["aktif_kullanici"]]["profil_fotografi"]))
                else ft.Icon(ft.Icons.PERSON, size=60, color=ft.Colors.CYAN_ACCENT)
            )),
            ft.TextButton("📷 Fotoğraf Değiştir", on_click=profil_fotografi_sec), ft.Container(height=20),
            isim_input, soyisim_input, yeni_sifre_input, ft.Container(height=20),
            ft.Button("💾 Profili Kaydet", on_click=profili_kaydet, width=320, height=55, style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))),
            ft.Container(height=10),
            ft.Button("🚪 Çıkış Yap", on_click=cikis_yap, width=320, height=55, style=ft.ButtonStyle(bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE, shape=ft.RoundedRectangleBorder(radius=10))),
            ft.Container(height=50)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
        
        page.add(ft.Container(content=profil_icerik, padding=20, expand=True))
        page.update()

    # Uygulama açılışında direkt Login'e yönlendir
    login_ekrani_goster()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
