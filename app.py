import os, sys, time, threading, ctypes, re, webbrowser
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

import lic
import tweaks
import config
import clip
import shortcut
from nui import *

WIN_SIZE = "1100x720"


class Activation(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=LIC_BG)
        self.app = app
        self.place(relwidth=1, relheight=1)
        logo(self, 64).pack(pady=(26, 0))
        card = ctk.CTkFrame(self, fg_color=LIC_CARD, corner_radius=18, border_width=1,
                            border_color=LIC_LINE, width=470, height=430)
        card.pack(pady=(14, 0))
        card.pack_propagate(False)
        ctk.CTkLabel(card, text="Lisans doğrulama", font=(FONT, 26, "bold"), text_color=TXT
                     ).pack(anchor="w", padx=36, pady=(32, 0))
        ctk.CTkLabel(card, text="Devam etmek için lisans anahtarını gir.", font=(FONT, 14),
                     text_color="#A1A1AA").pack(anchor="w", padx=36, pady=(2, 0))
        ctk.CTkLabel(card, text="Lisans anahtarı", font=(FONT, 13), text_color="#C4C4CC"
                     ).pack(anchor="w", padx=36, pady=(18, 0))
        self.key = ctk.CTkEntry(card, placeholder_text="NEXA-XXXX-XXXX-XXXX-XXXX",
                                height=50, corner_radius=10, fg_color=LIC_FIELD, border_width=1,
                                border_color=LIC_FIELD_LINE, text_color=TXT,
                                placeholder_text_color="#5E5E68", font=("Consolas", 13))
        self.key.pack(fill="x", padx=36, pady=(6, 0))
        enable_paste(self.key, "key")
        self.key.bind("<Return>", lambda _e: self.activate())
        self.remember = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card, text="Beni hatırla", variable=self.remember, fg_color="#FFFFFF",
                        hover_color="#D4D4D8", checkmark_color="#0B0B0D", border_color="#52525B",
                        text_color="#C4C4CC", font=(FONT, 14), checkbox_width=24, checkbox_height=24,
                        corner_radius=6).pack(anchor="w", padx=36, pady=(16, 0))
        self.btn = ctk.CTkButton(card, text="Giriş yap", command=self.activate, height=48, corner_radius=10,
                                 fg_color="#FFFFFF", hover_color="#E4E4E7", text_color="#0B0B0D",
                                 font=(FONT, 15, "bold"))
        self.btn.pack(fill="x", padx=36, pady=(16, 0))
        self.msg = ctk.CTkLabel(card, text=DEF_MSG, font=(FONT, 13), text_color="#71717A")
        self.msg.pack(pady=(14, 0))
        hrow = ctk.CTkFrame(card, fg_color="transparent")
        hrow.pack(pady=(10, 0))
        ctk.CTkLabel(hrow, text="HWID", font=(FONT, 11, "bold"), text_color="#71717A").pack(side="left")
        self.hw = ctk.CTkLabel(hrow, text="Okunuyor...", font=("Consolas", 12), text_color="#A1A1AA")
        self.hw.pack(side="left", padx=8)
        self.copy_btn = ctk.CTkButton(hrow, text="Kopyala", width=72, height=22, fg_color=LIC_FIELD,
                                      hover_color=LINE, text_color=TXT, font=(FONT, 11), command=self.copy)
        self.copy_btn.pack(side="left")
        links = ctk.CTkFrame(self, fg_color="transparent")
        links.pack(pady=(22, 0))
        for txt, cmd in (("Anahtar satın al", lambda: self.open_link(config.BUY_URL)),
                         ("Destek", lambda: self.open_link(config.SUPPORT_URL))):
            ctk.CTkButton(links, text=txt, fg_color="transparent", hover_color=LIC_BG, text_color="#A1A1AA",
                          font=(FONT, 14), width=10, command=cmd).pack(side="left", padx=14)
        ctk.CTkLabel(self, text="Developer by Chivas", font=(FONT, 11), text_color="#52525B"
                     ).pack(side="bottom", pady=10)

    def open_link(self, url):
        if url:
            webbrowser.open(url)
        else:
            messagebox.showinfo("Nexa", "Bu bağlantı henüz ayarlanmadı.")

    def set_hwid(self, h):
        self.hw.configure(text=h)

    def copy(self):
        clip.set_text(self.app.hwid or "")
        self.copy_btn.configure(text="Kopyalandı")
        self.after(1200, lambda: self.copy_btn.configure(text="Kopyala"))

    def activate(self):
        key = self.key.get().strip()
        if not self.app.hwid or not key:
            return
        hw = self.app.hwid
        self.btn.configure(state="disabled", text="Doğrulanıyor...")
        self.msg.configure(text="Sunucuya bağlanılıyor...", text_color="#71717A")
        self.app.bg(lambda: lic.check(key, hw), lambda r: self.finish(r, key))

    def finish(self, r, key):
        self.btn.configure(state="normal", text="Giriş yap")
        if not r:
            self.msg.configure(text="Beklenmeyen bir hata oluştu.", text_color=AMBER)
            return
        state, m, info = r
        if state == "ok":
            if self.remember.get():
                lic.save_license(key)
            else:
                lic.clear_license()
            self.msg.configure(text=DEF_MSG, text_color="#71717A")
            self.app.open_menu(info, key)
        else:
            self.msg.configure(text=m, text_color=AMBER)


class Menu(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG)
        self.app = app
        self.place(relwidth=1, relheight=1)
        self.vars = {}
        self.body = None
        self.info = None
        self.tier = "V1"

    def build(self, info, tier=None):
        if self.body is not None:
            self.body.destroy()
        self.vars = {}
        self.info = info
        tier = tier or info["tier"]
        self.tier = tier
        self.body = ctk.CTkFrame(self, fg_color=BG)
        self.body.pack(fill="both", expand=True)
        top = ctk.CTkFrame(self.body, fg_color="transparent")
        top.pack(fill="x", padx=28, pady=(18, 6))
        logo(top, 56).pack(side="left")
        tf = ctk.CTkFrame(top, fg_color="transparent")
        tf.pack(side="left", padx=14)
        title(tf, 28).pack(anchor="w")
        ctk.CTkLabel(tf, text="Developer by Chivas  •  Nexa UI", font=(FONT, 11), text_color=MUT).pack(anchor="w")
        badge = ctk.CTkFrame(top, fg_color=PANEL, corner_radius=12, border_width=1, border_color=ACC)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text=tweaks.TIER_TITLES[info["tier"]], font=(FONT, 14, "bold"), text_color=ACC
                     ).pack(padx=16, pady=(8, 0))
        ctk.CTkLabel(badge, text="Süre: " + info["expires"], font=(FONT, 11), text_color=MUT
                     ).pack(padx=16, pady=(0, 8))
        names = tweaks.access(info["tier"])
        if len(names) > 1:
            seg = ctk.CTkSegmentedButton(
                top, values=names, command=lambda t: self.after(10, lambda: self.build(self.info, t)),
                fg_color=PANEL2, selected_color="#52525B", selected_hover_color="#63636B",
                unselected_color=PANEL2, unselected_hover_color=LINE, text_color=TXT,
                font=(FONT, 14, "bold"), height=40)
            seg.set(tier)
            seg.pack(side="right", padx=18)
        main = ctk.CTkFrame(self.body, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28, pady=(6, 10))
        left = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=16, border_width=1, border_color=LINE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        items = tweaks.tier_items(tier)
        v4 = tier == "V4"
        ctk.CTkLabel(left, text=("%s  (%d özellik)  •  istemediğini kapatabilirsin" % (
            tweaks.TIER_TITLES[tier], len(items))) if v4 else "Bu pakette olanlar  (%d özellik)" % len(items),
                     font=(FONT, 15, "bold"), text_color=TXT).pack(anchor="w", padx=18, pady=(14, 4))
        sc = ctk.CTkScrollableFrame(left, fg_color="transparent", scrollbar_button_color=PANEL2,
                                    scrollbar_button_hover_color=ACC)
        sc.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        for i, grp, name, desc in items:
            if v4:
                v = ctk.BooleanVar(value=True)
                self.vars["i:" + i] = v
                NRow(sc, name, desc, grp, v).pack(fill="x", pady=3, padx=4)
                continue
            r = ctk.CTkFrame(sc, fg_color=PANEL2, corner_radius=10)
            r.pack(fill="x", pady=3, padx=4)
            ctk.CTkLabel(r, text="✓", font=(FONT, 15, "bold"), text_color=ACC, width=28
                         ).grid(row=0, column=0, rowspan=2, padx=(10, 0))
            ctk.CTkLabel(r, text=name, font=(FONT, 13, "bold"), text_color=TXT, anchor="w"
                         ).grid(row=0, column=1, sticky="w", padx=6, pady=(6, 0))
            ctk.CTkLabel(r, text=desc, font=(FONT, 11), text_color=MUT, anchor="w"
                         ).grid(row=1, column=1, sticky="w", padx=6, pady=(0, 6))
            ctk.CTkLabel(r, text=grp, font=(FONT, 10, "bold"), text_color=MUT
                         ).grid(row=0, column=2, rowspan=2, padx=12)
            r.grid_columnconfigure(1, weight=1)
        right = ctk.CTkFrame(main, fg_color="transparent", width=310)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        games = tweaks.TIER_GAMES.get(tier, [])
        if games:
            gt = tweaks.game_table(tier)
            ctk.CTkLabel(right, text="Oyun profilleri", font=(FONT, 15, "bold"), text_color=TXT
                         ).pack(anchor="w", pady=(2, 4))
            gs = ctk.CTkScrollableFrame(right, fg_color="transparent", height=190 if len(games) > 3 else 150,
                                        scrollbar_button_color=PANEL2, scrollbar_button_hover_color=ACC)
            gs.pack(fill="x")
            for g in games:
                nm, ds, _ = gt[g]
                c = ctk.CTkFrame(gs, fg_color=PANEL, corner_radius=12, border_width=1, border_color=LINE)
                c.pack(fill="x", pady=3, padx=2)
                tx = ctk.CTkFrame(c, fg_color="transparent")
                tx.pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(tx, text=nm, font=(FONT, 14, "bold"), text_color=TXT).pack(anchor="w")
                ctk.CTkLabel(tx, text=ds, font=(FONT, 10), text_color=MUT, justify="left").pack(anchor="w")
                v = ctk.BooleanVar(value=True)
                self.vars["g:" + g] = v
                ctk.CTkSwitch(c, text="", variable=v, progress_color="#71717A", button_color=TXT,
                              fg_color=LINE, width=44).pack(side="right", padx=12)
        else:
            ctk.CTkLabel(right, text="Bu pakette oyun profili yok.\nV2 ve V3 paketlerinde bulunur.",
                         font=(FONT, 12), text_color=MUT, justify="left").pack(anchor="w", pady=10)
        ctk.CTkButton(right, text="TWEAKİ BAŞLAT", command=self.start, **BTN).pack(fill="x", pady=(14, 6))
        small = dict(GHOST)
        if v4:
            small["height"] = 34
            ctk.CTkButton(right, text="Hızlı Temizlik (yeniden başlatmadan)", command=self.quick, **small
                          ).pack(fill="x", pady=3)
        if tweaks.TIER_SCAN.get(tier):
            ctk.CTkButton(right, text="Sistem Taraması + BIOS Kontrolü", command=self.scan, **small
                          ).pack(fill="x", pady=3)
        ctk.CTkButton(right, text="GPU Önerileri", command=self.gpu, **small).pack(fill="x", pady=3)
        ctk.CTkButton(right, text="BIOS Rehberi", command=self.bios, **small).pack(fill="x", pady=3)
        ctk.CTkButton(right, text="Geri Yükleme Noktasını Aç", command=tweaks.open_restore, **small
                      ).pack(fill="x", pady=3)

    def start(self):
        skip = {k[2:] for k, v in self.vars.items() if k.startswith("i:") and not v.get()}
        games = [k[2:] for k, v in self.vars.items() if k.startswith("g:") and v.get()]
        if len(skip) >= len(tweaks.TIERS.get(self.tier, [])) and not games:
            return messagebox.showwarning("Nexa", "En az bir özellik seçin.")
        if not messagebox.askyesno("Nexa", "Tweak başlatılsın mı?\nİşlem sonunda bilgisayar otomatik "
                                           "yeniden başlatılacak.\nAçık işlerinizi kaydedin."):
            return
        self.app.show("Progress")
        self.app.pages["Progress"].start(self.tier, games, skip)

    def popup(self, name, size):
        w = ctk.CTkToplevel(self, fg_color=BG)
        w.title(name)
        w.geometry(size)
        w.attributes("-topmost", True)
        return w

    def quick(self):
        if not messagebox.askyesno("Nexa", "Hızlı temizlik başlatılsın mı?\nArka plan uygulamaları kapatılır, "
                                           "önbellekler ve geçici dosyalar silinir, RAM boşaltılır.\n"
                                           "Yeniden başlatma gerekmez."):
            return
        w = self.popup("Hızlı Temizlik", "600x470")
        ctk.CTkLabel(w, text="Hızlı Temizlik", font=(FONT, 22, "bold"), text_color=ACC).pack(pady=(18, 4))
        task = ctk.CTkLabel(w, text="Hazırlanıyor...", font=(FONT, 13), text_color=TXT)
        task.pack()
        bar = ctk.CTkProgressBar(w, width=520, height=12, fg_color=PANEL2, progress_color=ACC)
        bar.set(0)
        bar.pack(pady=10)
        log = ctk.CTkTextbox(w, width=540, height=290, fg_color=PANEL, border_color=LINE, border_width=1,
                             font=("Consolas", 12), text_color=MUT)
        log.pack(pady=4)
        log.configure(state="disabled")
        q, state = [], {"done": False}

        def cb(frac, name):
            q.append((frac, name))

        def work():
            try:
                tweaks.v4.quick_clean(cb)
            finally:
                state["done"] = True

        def poll():
            while q:
                frac, name = q.pop(0)
                bar.set(frac)
                if name.endswith("..."):
                    task.configure(text=name)
                    continue
                if name == "Tamamlandı":
                    task.configure(text="Tamamlandı")
                    continue
                mark = "!  " if name.startswith("!") else "✓  "
                log.configure(state="normal")
                log.insert("end", mark + name.lstrip("!") + "\n")
                log.see("end")
                log.configure(state="disabled")
            if state["done"] and not q:
                return
            w.after(120, poll)

        threading.Thread(target=work, daemon=True).start()
        poll()

    def gpu(self):
        w = self.popup("GPU Önerileri", "520x360")
        ctk.CTkLabel(w, text="Ekran Kartı Önerileri", font=(FONT, 22, "bold"), text_color=ACC
                     ).pack(pady=(20, 6))
        info = ctk.CTkLabel(w, text="Taranıyor...", font=(FONT, 13), text_color=TXT, justify="left")
        info.pack(padx=30, pady=6)

        def work():
            brand, names = tweaks.detect_gpu()
            tips = tweaks.gpu_tips(brand)
            text = ", ".join(names) + "\n\n" + tips[0] + "\n" + "\n".join("• " + t for t in tips[1:])
            w.after(0, lambda: info.configure(text=text))

        threading.Thread(target=work, daemon=True).start()

    def bios(self):
        if self.tier != "V4":
            return self.bios_basic()
        w = self.popup("BIOS Rehberi", "620x640")
        ctk.CTkLabel(w, text="Önerilen BIOS Ayarları", font=(FONT, 22, "bold"), text_color=ACC
                     ).pack(pady=(18, 6))
        txt = ("Genel\n"
               "• XMP / EXPO profilini AÇ (RAM tam hızında çalışsın)\n"
               "• Resizable BAR / Above 4G Decoding: AÇIK\n"
               "• PCIe slot hızı: Gen4/Gen5 (Auto yerine sabit)\n"
               "• TPM 2.0 ve Secure Boot: AÇIK kalmalı (Valorant / Vanguard)\n"
               "• Fan eğrisini sıcaklığa göre agresif ayarla\n\n"
               "Intel işlemci\n"
               "• Intel Speed Shift: AÇIK, C-State: kapalı veya C1E kapalı\n"
               "• Enhanced Intel SpeedStep: kapalı (sabit yüksek frekans için)\n"
               "• Güç limitleri (PL1/PL2): anakartın önerdiği en yüksek, sıcaklığa dikkat\n\n"
               "AMD işlemci\n"
               "• CPPC ve CPPC Preferred Cores: AÇIK\n"
               "• Precision Boost Overdrive: Auto / Enabled\n"
               "• Global C-State Control: kapalı (mikro takılmayı azaltır)\n\n"
               "Dikkat\n"
               "• Emin olmadığın ayara dokunma, değişiklik sonrası stabilite testi yap\n"
               "• Bu ayarlar Windows'tan değiştirilemez, BIOS ekranında elle yapılır")
        box = ctk.CTkScrollableFrame(w, fg_color="transparent", height=420)
        box.pack(fill="x", padx=20)
        ctk.CTkLabel(box, text=txt, font=(FONT, 13), text_color=TXT, justify="left", anchor="w"
                     ).pack(anchor="w", padx=10)
        ctk.CTkButton(w, text="BIOS'A YENİDEN BAŞLAT", width=320, command=tweaks.bios_restart,
                      **{k: v for k, v in BTN.items()}).pack(pady=18)

    def bios_basic(self):
        w = self.popup("BIOS Rehberi", "560x470")
        ctk.CTkLabel(w, text="Önerilen BIOS Ayarları", font=(FONT, 22, "bold"), text_color=ACC
                     ).pack(pady=(20, 8))
        txt = ("• XMP / EXPO profilini AÇ (RAM tam hızında çalışsın)\n"
               "• Resizable BAR / Above 4G Decoding: AÇIK\n"
               "• CPU güç modu: Performans / Maksimum performans\n"
               "• Intel Speed Shift / AMD CPPC: AÇIK\n"
               "• PCIe slot hızı: Gen4/Gen5 (Auto yerine sabit)\n"
               "• Fan eğrisini sıcaklığa göre agresif ayarla\n"
               "• TPM 2.0 ve Secure Boot: AÇIK kalmalı (Valorant / Vanguard)\n"
               "• Emin olmadığın ayara dokunma, değişiklik sonrası stabilite testi yap")
        ctk.CTkLabel(w, text=txt, font=(FONT, 13), text_color=TXT, justify="left").pack(padx=30, pady=6)
        ctk.CTkButton(w, text="BIOS'A YENİDEN BAŞLAT", width=320, command=tweaks.bios_restart,
                      **{k: v for k, v in BTN.items()}).pack(pady=20)

    def scan(self):
        w = self.popup("Sistem Taraması", "640x600")
        ctk.CTkLabel(w, text="Sistem Taraması", font=(FONT, 22, "bold"), text_color=ACC).pack(pady=(18, 4))
        status = ctk.CTkLabel(w, text="Taranıyor...", font=(FONT, 13), text_color=MUT)
        status.pack()
        box = ctk.CTkScrollableFrame(w, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=16, pady=10)

        def work():
            d = tweaks.scan()
            w.after(0, lambda: fill(d))

        def fill(d):
            status.configure(text="")
            if not d:
                status.configure(text="Tarama yapılamadı.")
                return
            s = tweaks.summary(d)
            for k, lab in (("cpu", "İşlemci"), ("gpu", "Ekran kartı"), ("ram", "RAM"), ("disk", "Disk")):
                r = ctk.CTkFrame(box, fg_color=PANEL, corner_radius=10)
                r.pack(fill="x", pady=3)
                ctk.CTkLabel(r, text=lab, font=(FONT, 12, "bold"), text_color=ACC, width=90, anchor="w"
                             ).pack(side="left", padx=12, pady=8)
                ctk.CTkLabel(r, text=s[k], font=(FONT, 12), text_color=TXT, justify="left", anchor="w"
                             ).pack(side="left", pady=8)
            colors = {"ok": GREEN, "warn": AMBER, "info": MUT}
            for nm, st, tx in tweaks.bios_checks(d):
                r = ctk.CTkFrame(box, fg_color=PANEL2, corner_radius=10)
                r.pack(fill="x", pady=3)
                ctk.CTkLabel(r, text="●", text_color=colors[st], font=(FONT, 14), width=28
                             ).pack(side="left", padx=(10, 0))
                tf = ctk.CTkFrame(r, fg_color="transparent")
                tf.pack(side="left", fill="x", expand=True, pady=6)
                ctk.CTkLabel(tf, text=nm, font=(FONT, 13, "bold"), text_color=TXT, anchor="w").pack(anchor="w")
                ctk.CTkLabel(tf, text=tx, font=(FONT, 11), text_color=MUT, anchor="w", justify="left",
                             wraplength=480).pack(anchor="w")

        threading.Thread(target=work, daemon=True).start()


class Progress(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG)
        self.app = app
        self.place(relwidth=1, relheight=1)
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.place(relx=.5, rely=.5, anchor="center")
        logo(box, 150).pack()
        title(box, 34, "TWEAK").pack(pady=(6, 0))
        ctk.CTkLabel(box, text="Optimizasyon sürüyor. İşlem bitene kadar bu ekran kapatılamaz.",
                     font=(FONT, 13), text_color=MUT).pack(pady=(6, 0))
        self.task = ctk.CTkLabel(box, text="Hazırlanıyor...", font=(FONT, 16, "bold"), text_color=TXT)
        self.task.pack(pady=(26, 8))
        self.bar = ctk.CTkProgressBar(box, width=680, height=16, corner_radius=8, fg_color=PANEL2,
                                      progress_color=ACC)
        self.bar.set(0)
        self.bar.pack()
        row = ctk.CTkFrame(box, fg_color="transparent")
        row.pack(fill="x", pady=(10, 0))
        self.step = ctk.CTkLabel(row, text="Adım 0 / 0", font=(FONT, 13), text_color=MUT)
        self.step.pack(side="left")
        self.pct = ctk.CTkLabel(row, text="%0", font=(FONT, 30, "bold"), text_color=ACC)
        self.pct.pack(side="right")
        self.log = ctk.CTkTextbox(box, width=680, height=200, fg_color=PANEL, border_color=LINE,
                                  border_width=1, font=("Consolas", 12), text_color=MUT)
        self.log.pack(pady=(12, 0))
        self.log.configure(state="disabled")
        footer(self)

    def start(self, tier, games, skip=None):
        self.app.lock()
        self.target = 0.0
        self.shown = 0.0
        self.text = "Hazırlanıyor..."
        self.done = False
        self.events = []
        self.finished = 0
        self.total = len(tweaks.plan(tier, games, skip))
        self.end_delay = 2500 if tier == "V4" else 700
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        threading.Thread(target=self.work, args=(tier, games, skip), daemon=True).start()
        self.animate()

    def work(self, tier, games, skip):
        def cb(frac, name):
            self.target = frac
            if name.startswith("#"):
                self.events.append(("info", name[1:]))
            elif name.startswith("!"):
                self.events.append(("bad", name[1:]))
            elif name.endswith("..."):
                self.text = name
            elif name == "Tamamlandı":
                self.text = name
            else:
                self.events.append(("ok", name))
        try:
            tweaks.run_all(tier, games, cb, skip)
        finally:
            self.done = True

    def animate(self):
        while self.events:
            kind, n = self.events.pop(0)
            if kind != "info":
                self.finished += 1
            self.log.configure(state="normal")
            self.log.insert("end", {"ok": "✓  ", "bad": "!  ", "info": "•  "}[kind] + n + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        d = self.target - self.shown
        self.shown += d * 0.12 if abs(d) > 0.002 else d
        self.bar.set(self.shown)
        self.pct.configure(text="%" + str(int(self.shown * 100)))
        self.task.configure(text=self.text)
        self.step.configure(text="Adım %d / %d" % (min(self.finished, self.total), self.total))
        if self.done and self.shown > 0.995:
            self.bar.set(1)
            self.pct.configure(text="%100")
            self.after(self.end_delay, lambda: (self.app.show("Countdown"), self.app.pages["Countdown"].start()))
            return
        self.after(16, self.animate)


class Countdown(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG)
        self.app = app
        self.place(relwidth=1, relheight=1)
        box = ctk.CTkFrame(self, fg_color="transparent")
        box.place(relx=.5, rely=.5, anchor="center")
        logo(box, 130).pack()
        ctk.CTkLabel(box, text="Developer By Chivas", font=(FONT, 52, "bold"), text_color=TXT).pack()
        self.info = ctk.CTkLabel(box, text="Sistem yeniden başlatılıyor", font=(FONT, 15), text_color=MUT)
        self.info.pack(pady=(4, 0))
        self.num = ctk.CTkLabel(box, text="5", font=(FONT, 120, "bold"), text_color=ACC)
        self.num.pack(pady=(10, 6))
        self.bar = ctk.CTkProgressBar(box, width=680, height=16, corner_radius=8, fg_color=PANEL2,
                                      progress_color=ACC)
        self.bar.set(0)
        self.bar.pack()

    def start(self):
        self.n = 5
        self.tick()

    def tick(self):
        if self.n == 0:
            tweaks.reboot_now()
            self.info.configure(text="Yeniden başlatma bekleniyor...")
            self.after(20000, self.fallback)
            return
        self.num.configure(text=str(self.n))
        self.bar.set((5 - self.n + 1) / 5)
        self.n -= 1
        self.after(1000, self.tick)

    def fallback(self):
        self.app.unlock()
        self.app.show("Menu")
        messagebox.showinfo("Nexa", "Otomatik yeniden başlatma yapılamadı. Değişikliklerin etkili olması "
                                    "için bilgisayarı elle yeniden başlatın.")


class AdminLogin(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=LIC_BG)
        self.app = app
        self.place(relwidth=1, relheight=1)
        logo(self, 64).pack(pady=(70, 0))
        card = ctk.CTkFrame(self, fg_color=LIC_CARD, corner_radius=18, border_width=1,
                            border_color=LIC_LINE, width=470, height=340)
        card.pack(pady=(14, 0))
        card.pack_propagate(False)
        ctk.CTkLabel(card, text="Admin girişi", font=(FONT, 26, "bold"), text_color=TXT
                     ).pack(anchor="w", padx=36, pady=(32, 0))
        ctk.CTkLabel(card, text="Devam etmek için admin şifreni gir.", font=(FONT, 14),
                     text_color="#A1A1AA").pack(anchor="w", padx=36, pady=(2, 0))
        ctk.CTkLabel(card, text="Admin şifresi", font=(FONT, 13), text_color="#C4C4CC"
                     ).pack(anchor="w", padx=36, pady=(18, 0))
        self.pw = ctk.CTkEntry(card, placeholder_text="Şifre", show="•", height=50, corner_radius=10,
                               fg_color=LIC_FIELD, border_width=1, border_color=LIC_FIELD_LINE,
                               text_color=TXT, placeholder_text_color="#5E5E68", font=(FONT, 14))
        self.pw.pack(fill="x", padx=36, pady=(6, 0))
        enable_paste(self.pw, "raw")
        self.pw.bind("<Return>", lambda _e: self.login())
        self.btn = ctk.CTkButton(card, text="Giriş yap", command=self.login, height=48, corner_radius=10,
                                 fg_color="#FFFFFF", hover_color="#E4E4E7", text_color="#0B0B0D",
                                 font=(FONT, 15, "bold"))
        self.btn.pack(fill="x", padx=36, pady=(18, 0))
        self.msg = ctk.CTkLabel(card, text="", font=(FONT, 13), text_color=AMBER)
        self.msg.pack(pady=(14, 0))
        ctk.CTkLabel(self, text="Developer by Chivas", font=(FONT, 11), text_color="#52525B"
                     ).pack(side="bottom", pady=10)

    def login(self):
        token = self.pw.get().strip()
        if not token:
            return
        self.btn.configure(state="disabled", text="Doğrulanıyor...")
        self.msg.configure(text="", text_color=AMBER)
        self.app.bg(lambda: lic.admin_login(token), lambda r: self.finish(r, token))

    def finish(self, r, token):
        self.btn.configure(state="normal", text="Giriş yap")
        if not r:
            self.msg.configure(text="Beklenmeyen bir hata oluştu.")
            return
        ok, m, items = r
        if not ok:
            self.msg.configure(text=m)
            return
        self.pw.delete(0, "end")
        self.msg.configure(text="")
        self.app.admin_token = token
        self.app.pages["Admin"].render(items)
        self.app.show("Admin")


def fmt_ms(ms):
    return time.strftime("%d.%m.%Y", time.localtime(ms / 1000))


def status_of(r):
    if r.get("expires") and time.time() * 1000 > r["expires"]:
        return "Süresi doldu"
    if r.get("hwid"):
        return "Kullanıldı"
    return "Bekliyor"


class Admin(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=BG)
        self.app = app
        self.place(relwidth=1, relheight=1)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=22, pady=(14, 4))
        logo(top, 44).pack(side="left")
        title(top, 24, "ADMIN").pack(side="left", padx=12)
        ctk.CTkButton(top, text="Çıkış", width=80, command=self.logout, **GHOST).pack(side="right")
        ctk.CTkButton(top, text="Yenile", width=80, command=self.refresh, **GHOST).pack(side="right", padx=8)
        self.stats = ctk.CTkLabel(top, text="", font=(FONT, 12), text_color=MUT)
        self.stats.pack(side="right", padx=16)
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=22, pady=(4, 6))
        left = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=16, width=350, border_width=1, border_color=LINE)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        ctk.CTkLabel(left, text="Yeni Key", font=(FONT, 17, "bold"), text_color=TXT
                     ).pack(anchor="w", padx=20, pady=(16, 6))
        self.name = entry(left, "Müşteri adı")
        self.name.pack(fill="x", padx=20, pady=4)
        enable_paste(self.name, "text")
        self.tier = ctk.CTkSegmentedButton(left, values=list(lic.TIERS), fg_color=PANEL2,
                                           selected_color="#52525B", selected_hover_color="#63636B",
                                           unselected_color=PANEL2, unselected_hover_color=LINE,
                                           text_color=TXT, font=(FONT, 14, "bold"), height=40)
        self.tier.set("V4")
        self.tier.pack(fill="x", padx=20, pady=6)
        self.days = entry(left, "Süre (gün)  0 = sınırsız")
        self.days.insert(0, "0")
        self.days.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(left, text="Süre, müşteri keyi ilk kullandığında başlar.", font=(FONT, 11),
                     text_color=MUT).pack(anchor="w", padx=22)
        self.create_btn = ctk.CTkButton(left, text="KEY OLUŞTUR", command=self.create, **BTN)
        self.create_btn.pack(fill="x", padx=20, pady=(10, 8))
        self.status = ctk.CTkLabel(left, text="", font=(FONT, 11), text_color=GREEN, wraplength=300)
        self.status.pack(anchor="w", padx=20)
        self.out = ctk.CTkTextbox(left, height=60, fg_color=PANEL2, border_color=LIC_FIELD_LINE, border_width=1,
                                  font=("Consolas", 16, "bold"), text_color=TXT, wrap="char")
        self.out.pack(fill="x", padx=20, pady=(6, 6))
        ctk.CTkButton(left, text="Key'i Kopyala", command=self.copy_out, **GHOST).pack(fill="x", padx=20, pady=4)
        right = ctk.CTkFrame(main, fg_color=PANEL, corner_radius=16, border_width=1, border_color=LINE)
        right.pack(side="right", fill="both", expand=True)
        ctk.CTkLabel(right, text="Key Yönetimi", font=(FONT, 17, "bold"), text_color=TXT
                     ).pack(anchor="w", padx=20, pady=(16, 6))
        self.listf = ctk.CTkScrollableFrame(right, fg_color="transparent", scrollbar_button_color=PANEL2,
                                            scrollbar_button_hover_color=ACC)
        self.listf.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        footer(self)

    def logout(self):
        self.app.admin_token = None
        self.app.destroy()

    def note(self, text, good=True):
        self.status.configure(text=text, text_color=GREEN if good else AMBER)

    def create(self):
        name = self.name.get().strip()
        tier = self.tier.get()
        if not name:
            return messagebox.showwarning("Nexa", "Müşteri adı girin.")
        try:
            days = int(self.days.get().strip() or 0)
        except ValueError:
            return messagebox.showwarning("Nexa", "Süre sayı olmalı.")
        token = self.app.admin_token
        self.create_btn.configure(state="disabled", text="Oluşturuluyor...")
        self.app.bg(lambda: lic.admin_create(token, name, tier, days), lambda r: self.created(r, tier))

    def created(self, r, tier):
        self.create_btn.configure(state="normal", text="KEY OLUŞTUR")
        if not r:
            return self.note("Beklenmeyen hata.", False)
        key, err = r
        if err:
            return self.note(err, False)
        self.show_key(key)
        self.note("✓ %s key oluşturuldu. Tek kullanımlık, ilk girişte o bilgisayara kilitlenir." % tier)
        self.name.delete(0, "end")
        self.refresh()

    def show_key(self, key):
        self.out.delete("1.0", "end")
        self.out.insert("1.0", key)

    def copy_text(self, text):
        text = (text or "").strip()
        if not text:
            return
        self.note("✓ Kopyalandı." if clip.set_text(text) else "Kopyalanamadı.", clip.get_text() == text)

    def copy_out(self):
        self.copy_text(self.out.get("1.0", "end"))

    def refresh(self):
        token = self.app.admin_token
        self.app.bg(lambda: lic.admin_list(token), self.refreshed)

    def refreshed(self, r):
        if not r:
            return
        items, err = r
        if err:
            return self.note(err, False)
        self.render(items)

    def act(self, action, key, confirm):
        if not messagebox.askyesno("Nexa", confirm):
            return
        token = self.app.admin_token
        self.app.bg(lambda: lic.admin_action(token, action, key), lambda r: self.acted(r, action))

    def acted(self, r, action):
        if not r or not r[0]:
            return self.note((r[1] if r else "") or "İşlem başarısız.", False)
        self.note("✓ Key silindi. Müşteri yaklaşık 1-2 dakika içinde sistemden atılır."
                  if action == "delete" else "✓ HWID sıfırlandı. Key yeni bilgisayarda kullanılabilir.")
        self.refresh()

    def render(self, items):
        counts = {t: sum(1 for r in items if r.get("tier") == t) for t in lic.TIERS}
        used = sum(1 for r in items if r.get("hwid"))
        self.stats.configure(text="Toplam %d  •  %s  •  Kullanılan %d" % (
            len(items), "  ".join("%s %d" % (t, counts[t]) for t in lic.TIERS), used))
        for w in self.listf.winfo_children():
            w.destroy()
        colors = {"Bekliyor": AMBER, "Kullanıldı": GREEN, "Süresi doldu": "#71717A"}
        for r in items:
            st = status_of(r)
            row = ctk.CTkFrame(self.listf, fg_color=PANEL2, corner_radius=10)
            row.pack(fill="x", pady=4, padx=2)
            head = ctk.CTkFrame(row, fg_color="transparent")
            head.pack(fill="x", padx=12, pady=(8, 0))
            ctk.CTkLabel(head, text=r.get("name", "?"), font=(FONT, 14, "bold"), text_color=TXT).pack(side="left")
            ctk.CTkLabel(head, text=r.get("tier", "?"), font=(FONT, 11, "bold"), text_color=DARK, fg_color=ACC,
                         corner_radius=6, width=34).pack(side="left", padx=8)
            ctk.CTkLabel(head, text=st, font=(FONT, 11, "bold"), text_color=colors.get(st, MUT)).pack(side="right")
            if r.get("expires"):
                exp = fmt_ms(r["expires"])
            elif r.get("days"):
                exp = "%d gün (ilk girişte başlar)" % r["days"]
            else:
                exp = "Sınırsız"
            ctk.CTkLabel(row, text="Oluşturma: %s  •  Bitiş: %s" % (fmt_ms(r.get("created", 0)), exp),
                         font=("Consolas", 10), text_color=MUT, anchor="w").pack(fill="x", padx=12)
            ctk.CTkLabel(row, text="HWID: %s" % (r.get("hwid") or "henüz kullanılmadı"),
                         font=("Consolas", 10), text_color=MUT, anchor="w").pack(fill="x", padx=12)
            ctk.CTkLabel(row, text=r["key"], font=("Consolas", 14, "bold"), text_color=ACC,
                         anchor="w").pack(fill="x", padx=12, pady=(2, 0))
            btns = ctk.CTkFrame(row, fg_color="transparent")
            btns.pack(fill="x", padx=10, pady=(4, 8))
            for txt, cmd in (("Kopyala", lambda k=r["key"]: self.copy_text(k)),
                             ("HWID sıfırla", lambda k=r["key"]: self.act(
                                 "reset", k, "Bu key'in bilgisayar kilidi kaldırılsın mı?")),
                             ("Sil", lambda k=r["key"]: self.act(
                                 "delete", k, "Key silinsin mi? Müşteri sistemden atılır."))):
                ctk.CTkButton(btns, text=txt, width=96, height=26, fg_color=PANEL, hover_color=LINE,
                              text_color=TXT, font=(FONT, 11), command=cmd).pack(side="left", padx=3)


class App(ctk.CTk):
    def __init__(self):
        super().__init__(fg_color=BG)
        ctk.set_appearance_mode("dark")
        self.title("Nexa Tweak • Developer by Chivas")
        self.geometry(WIN_SIZE)
        self.resizable(False, False)
        try:
            self.iconbitmap(res("assets/icon.ico"))
        except Exception:
            pass
        self.hwid = None
        self.admin_token = None
        self.license_key = None
        self.locked = False
        self.current = ""
        self.recheck_job = None
        box = ctk.CTkFrame(self, fg_color=BG)
        box.pack(fill="both", expand=True)
        self.pages = {n: c(box, self) for n, c in (
            ("Activation", Activation), ("Menu", Menu), ("Progress", Progress),
            ("Countdown", Countdown), ("AdminLogin", AdminLogin), ("Admin", Admin))}
        self.admin_mode = lic.admin_mode()
        if self.admin_mode:
            self.title("Nexa Admin • Developer by Chivas")
            self.show("AdminLogin")
            self.pages["AdminLogin"].pw.focus_set()
        else:
            self.show("Activation")
            threading.Thread(target=self.read_hw, daemon=True).start()
            threading.Thread(target=shortcut.ensure, daemon=True).start()

    def bg(self, fn, cb):
        def run():
            try:
                r = fn()
            except Exception:
                r = None
            try:
                self.after(0, lambda: cb(r))
            except Exception:
                pass
        threading.Thread(target=run, daemon=True).start()

    def show(self, n):
        self.current = n
        self.pages[n].tkraise()

    def lock(self):
        self.locked = True
        self.resizable(True, True)
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self.bind_all("<Alt-F4>", lambda _e: "break")
        self.bind_all("<Escape>", lambda _e: "break")
        self.keep_front()

    def keep_front(self):
        if not self.locked:
            return
        try:
            self.deiconify()
            self.attributes("-topmost", True)
            self.lift()
            self.focus_force()
        except Exception:
            pass
        self.after(600, self.keep_front)

    def unlock(self):
        self.locked = False
        try:
            self.attributes("-topmost", False)
            self.attributes("-fullscreen", False)
            self.protocol("WM_DELETE_WINDOW", self.destroy)
            self.geometry(WIN_SIZE)
            self.resizable(False, False)
        except Exception:
            pass

    def open_menu(self, info, key):
        self.license_key = key
        self.pages["Menu"].build(info)
        self.show("Menu")
        self.schedule_recheck()

    def schedule_recheck(self):
        if self.recheck_job:
            try:
                self.after_cancel(self.recheck_job)
            except Exception:
                pass
        self.recheck_job = self.after(config.RECHECK_SECONDS * 1000, self.recheck)

    def busy(self):
        return self.locked or self.current in ("Progress", "Countdown")

    def recheck(self):
        self.recheck_job = None
        if not self.license_key:
            return
        if self.busy():
            self.schedule_recheck()
            return
        key, hw = self.license_key, self.hwid
        self.bg(lambda: lic.check(key, hw), self.recheck_done)

    def recheck_done(self, r):
        if not self.license_key:
            return
        if r and r[0] == "denied" and not self.busy():
            self.kick(r[1])
            return
        self.schedule_recheck()

    def kick(self, msg):
        lic.clear_license()
        self.license_key = None
        act = self.pages["Activation"]
        act.key.delete(0, "end")
        act.msg.configure(text="Lisansın geçersiz: " + msg, text_color=AMBER)
        self.show("Activation")

    def read_hw(self):
        self.hwid = lic.get_hwid()
        self.after(0, self.ready)

    def ready(self):
        if self.admin_mode:
            return
        act = self.pages["Activation"]
        act.set_hwid(self.hwid)
        saved = lic.load_license()
        if saved:
            act.msg.configure(text="Lisans doğrulanıyor...", text_color="#71717A")
            hw = self.hwid
            self.bg(lambda: lic.check(saved, hw), lambda r: self.saved_done(r, saved))

    def saved_done(self, r, saved):
        act = self.pages["Activation"]
        if not r:
            act.msg.configure(text=DEF_MSG, text_color="#71717A")
            return
        state, m, info = r
        if state == "ok":
            self.open_menu(info, saved)
            return
        if state == "denied":
            lic.clear_license()
        else:
            act.key.insert(0, saved)
            act.remember.set(True)
        act.msg.configure(text=m, text_color=AMBER)


if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        messagebox.showerror("Nexa", "Yönetici olarak çalıştırın.")
        sys.exit()
    App().mainloop()
