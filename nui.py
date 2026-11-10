"""NUI - Nexa UI: Nexa Tweak'in ortak arayüz altyapısı (tema, bileşenler, pano desteği)."""
import os
import sys
import tkinter as tk

import customtkinter as ctk
from PIL import Image

import clip

NUI_VERSION = "1.0"

BG = "#0B0B0D"
PANEL = "#111113"
PANEL2 = "#18181B"
LINE = "#2A2A30"
ACC = "#FFFFFF"
ACC_D = "#D4D4D8"
TXT = "#FFFFFF"
MUT = "#A1A1AA"
GREEN = "#4ADE80"
DARK = "#0B0B0D"
LIC_BG = "#0B0B0D"
LIC_CARD = "#111113"
LIC_LINE = "#2A2A30"
LIC_FIELD = "#18181B"
LIC_FIELD_LINE = "#8E8E96"
AMBER = "#FBBF24"
FONT = "Segoe UI"
DEF_MSG = "Anahtar sunucuda doğrulanır."
BTN = dict(height=48, corner_radius=10, fg_color=ACC, hover_color=ACC_D, text_color=DARK,
           font=(FONT, 15, "bold"))
GHOST = dict(height=40, corner_radius=10, fg_color="transparent", border_width=1, border_color="#3F3F46",
             hover_color=PANEL2, text_color=TXT, font=(FONT, 13, "bold"))


def res(p):
    return os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))), p)


_L = Image.open(res("assets/logo.png"))


def logo(parent, h):
    w = int(h * _L.width / _L.height)
    return ctk.CTkLabel(parent, text="", image=ctk.CTkImage(_L, size=(w, h)))


def title(parent, size, right="TWEAK"):
    f = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(f, text="NEXA ", font=(FONT, size, "bold"), text_color=TXT).pack(side="left")
    ctk.CTkLabel(f, text=right, font=(FONT, size, "bold"), text_color=MUT).pack(side="left")
    return f


def footer(parent):
    ctk.CTkLabel(parent, text="Developer by Chivas", font=(FONT, 12), text_color=MUT
                 ).pack(side="bottom", pady=12)


def entry(parent, ph, show=None, font=(FONT, 13)):
    return ctk.CTkEntry(parent, placeholder_text=ph, height=44, fg_color=PANEL2, border_color=LINE,
                        text_color=TXT, placeholder_text_color=MUT, font=font, show=show)


def enable_paste(e, mode="text"):
    def clean(v):
        if mode == "key":
            return "".join(v.split())
        if mode == "raw":
            return v.strip()
        return " ".join(v.split())

    def paste(_ev=None):
        v = clip.get_text()
        if not v:
            try:
                v = e.winfo_toplevel().clipboard_get()
            except Exception:
                v = ""
        v = clean(v)
        if not v:
            return "break"
        try:
            e.delete("sel.first", "sel.last")
        except Exception:
            pass
        e.insert("insert", v)
        return "break"

    def copy_sel(_ev=None):
        try:
            t = e._entry.selection_get()
        except Exception:
            t = ""
        if t:
            clip.set_text(t)
        return "break"

    def select_all(_ev=None):
        try:
            e._entry.select_range(0, "end")
            e._entry.icursor("end")
        except Exception:
            pass
        return "break"

    def menu(ev):
        m = tk.Menu(e, tearoff=0)
        m.add_command(label="Yapıştır", command=paste)
        m.add_command(label="Kopyala", command=copy_sel)
        m.add_command(label="Tümünü seç", command=select_all)
        try:
            m.tk_popup(ev.x_root, ev.y_root)
        finally:
            m.grab_release()

    for seq in ("<Control-v>", "<Control-V>", "<Shift-Insert>"):
        e.bind(seq, paste)
    for seq in ("<Control-c>", "<Control-C>"):
        e.bind(seq, copy_sel)
    for seq in ("<Control-a>", "<Control-A>"):
        e.bind(seq, select_all)
    e.bind("<Button-3>", menu)


class NRow(ctk.CTkFrame):
    """Nexa UI satırı: solda anahtar, ortada ad + açıklama, sağda grup etiketi."""

    def __init__(self, parent, name, desc, group, var):
        super().__init__(parent, fg_color=PANEL2, corner_radius=10)
        ctk.CTkSwitch(self, text="", variable=var, progress_color="#71717A", button_color=TXT,
                      fg_color=LINE, width=44).grid(row=0, column=0, rowspan=2, padx=(10, 2))
        ctk.CTkLabel(self, text=name, font=(FONT, 13, "bold"), text_color=TXT, anchor="w"
                     ).grid(row=0, column=1, sticky="w", padx=6, pady=(6, 0))
        ctk.CTkLabel(self, text=desc, font=(FONT, 11), text_color=MUT, anchor="w"
                     ).grid(row=1, column=1, sticky="w", padx=6, pady=(0, 6))
        ctk.CTkLabel(self, text=group, font=(FONT, 10, "bold"), text_color=MUT
                     ).grid(row=0, column=2, rowspan=2, padx=12)
        self.grid_columnconfigure(1, weight=1)
