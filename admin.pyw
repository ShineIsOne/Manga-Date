#!/usr/bin/env python3
"""
Manga Schedule Admin Tool
Edit data manga dan push langsung ke index.html
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import json
import re
import os
import subprocess
import sys
from datetime import datetime

# ── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT   = "#fee715"
BG       = "#111820"
SURFACE  = "#18222e"
SURFACE2 = "#1e2d3d"
BORDER   = "#2a3d52"
TEXT     = "#f0eedc"
TEXT_DIM = "#7a8fa6"
RED      = "#e63946"
GREEN    = "#2ec27e"

MONTHS = ['Januari','Februari','Maret','April','Mei','Juni',
          'Juli','Agustus','September','Oktober','November','Desember']
MONTHS_SHORT = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']

# Path default index.html (folder yang sama dengan script ini)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_HTML = os.path.join(SCRIPT_DIR, "index.html")

def gen_id():
    import time, random, string
    t = int(time.time() * 1000)
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return f"adm{t}{r}"

# ── Baca/tulis HTML ───────────────────────────────────────────────────────────
def load_from_html(html_path):
    """Baca MANGA_DATA dari index.html"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'const MANGA_DATA = (\[.*?\]);', content, re.DOTALL)
        if m:
            return json.loads(m.group(1))
    except Exception as e:
        messagebox.showerror("Error", f"Gagal baca HTML:\n{e}")
    return []

def save_to_html(html_path, data):
    """Tulis MANGA_DATA ke index.html"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        new_content = re.sub(
            r'const MANGA_DATA = \[.*?\];',
            f'const MANGA_DATA = {new_data};',
            content, flags=re.DOTALL
        )
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Gagal simpan HTML:\n{e}")
        return False

def git_push(html_path):
    """Git add + commit + push"""
    try:
        repo_dir = os.path.dirname(html_path)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cmds = [
            ["git", "-C", repo_dir, "add", os.path.basename(html_path)],
            ["git", "-C", repo_dir, "commit", "-m", f"Update manga data {now}"],
            ["git", "-C", repo_dir, "push"],
        ]
        for cmd in cmds:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0 and "nothing to commit" not in result.stdout:
                return False, result.stderr or result.stdout
        return True, "Push berhasil!"
    except FileNotFoundError:
        return False, "Git tidak ditemukan. Pastikan Git terinstall."
    except Exception as e:
        return False, str(e)

# ── Dialog Tambah/Edit ────────────────────────────────────────────────────────
class MangaDialog(ctk.CTkToplevel):
    def __init__(self, parent, manga=None):
        super().__init__(parent)
        self.title("Edit Manga" if manga else "Tambah Manga")
        self.geometry("520x520")
        self.resizable(False, False)
        self.configure(fg_color=SURFACE)
        self.grab_set()
        self.result = None

        now = datetime.now()
        m = manga or {}

        pad = {"padx": 20, "pady": 6}

        # Title
        ctk.CTkLabel(self, text="JUDUL MANGA", font=("Space Mono", 11),
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(20,2))
        self.e_title = ctk.CTkEntry(self, placeholder_text="Judul manga...",
                                    fg_color=SURFACE2, border_color=BORDER,
                                    text_color=TEXT, font=("Noto Sans JP", 14), height=40)
        self.e_title.pack(fill="x", **pad)
        if m.get("title"): self.e_title.insert(0, m["title"])

        # Link
        ctk.CTkLabel(self, text="LINK", font=("Space Mono", 11),
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(8,2))
        self.e_link = ctk.CTkEntry(self, placeholder_text="https://...",
                                   fg_color=SURFACE2, border_color=BORDER,
                                   text_color=TEXT, font=("Space Mono", 11), height=36)
        self.e_link.pack(fill="x", **pad)
        if m.get("link"): self.e_link.insert(0, m["link"])

        # Tanggal row
        ctk.CTkLabel(self, text="TANGGAL UPDATE", font=("Space Mono", 11),
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(8,2))

        date_frame = ctk.CTkFrame(self, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=6)
        date_frame.columnconfigure((0,1,2), weight=1)

        # Day
        ctk.CTkLabel(date_frame, text="Tanggal", font=("Space Mono", 10),
                     text_color=TEXT_DIM).grid(row=0, column=0, sticky="w")
        self.e_day = ctk.CTkEntry(date_frame, placeholder_text="1–31 / Awal / Akhir",
                                  fg_color=SURFACE2, border_color=BORDER,
                                  text_color=ACCENT, font=("Space Mono", 12), height=36)
        self.e_day.grid(row=1, column=0, sticky="ew", padx=(0,6))
        if m.get("dayStr"): self.e_day.insert(0, m["dayStr"])

        # Month
        ctk.CTkLabel(date_frame, text="Bulan", font=("Space Mono", 10),
                     text_color=TEXT_DIM).grid(row=0, column=1, sticky="w")
        self.om_month = ctk.CTkOptionMenu(date_frame, values=MONTHS,
                                          fg_color=SURFACE2, button_color=SURFACE2,
                                          button_hover_color=BORDER, dropdown_fg_color=SURFACE2,
                                          text_color=TEXT, font=("Space Mono", 12), height=36)
        self.om_month.grid(row=1, column=1, sticky="ew", padx=3)
        self.om_month.set(MONTHS[m.get("month", now.month)-1])

        # Year
        ctk.CTkLabel(date_frame, text="Tahun", font=("Space Mono", 10),
                     text_color=TEXT_DIM).grid(row=0, column=2, sticky="w")
        years = [str(now.year + i) for i in range(4)]
        self.om_year = ctk.CTkOptionMenu(date_frame, values=years,
                                         fg_color=SURFACE2, button_color=SURFACE2,
                                         button_hover_color=BORDER, dropdown_fg_color=SURFACE2,
                                         text_color=TEXT, font=("Space Mono", 12), height=36)
        self.om_year.grid(row=1, column=2, sticky="ew", padx=(6,0))
        self.om_year.set(str(m.get("year", now.year)))

        # Flags
        ctk.CTkLabel(self, text="TERSEDIA DI", font=("Space Mono", 11),
                     text_color=TEXT_DIM).pack(anchor="w", padx=20, pady=(8,2))
        flags_frame = ctk.CTkFrame(self, fg_color="transparent")
        flags_frame.pack(anchor="w", padx=20, pady=4)
        cur_flags = m.get("flags", ["id"])
        self.var_id = tk.BooleanVar(value="id" in cur_flags)
        self.var_en = tk.BooleanVar(value="en" in cur_flags)
        ctk.CTkCheckBox(flags_frame, text="🇮🇩  IDN (Indonesia)", variable=self.var_id,
                        text_color=TEXT, fg_color=RED, hover_color="#c02030",
                        font=("Space Mono", 12)).pack(side="left", padx=(0,20))
        ctk.CTkCheckBox(flags_frame, text="🇬🇧  ENG (English)", variable=self.var_en,
                        text_color=TEXT, fg_color="#2a6aad", hover_color="#1e5090",
                        font=("Space Mono", 12)).pack(side="left")

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(16,20))
        ctk.CTkButton(btn_frame, text="BATAL", fg_color=SURFACE2, hover_color=BORDER,
                      text_color=TEXT_DIM, font=("Space Mono", 12), height=40,
                      command=self.destroy).pack(side="left", expand=True, fill="x", padx=(0,8))
        ctk.CTkButton(btn_frame, text="SIMPAN", fg_color=ACCENT, hover_color="#fff875",
                      text_color=BG, font=("Space Mono", 13, "bold"), height=40,
                      command=self._save).pack(side="left", expand=True, fill="x")

    def _save(self):
        title = self.e_title.get().strip()
        if not title:
            self.e_title.configure(border_color=RED)
            return
        flags = []
        if self.var_id.get(): flags.append("id")
        if self.var_en.get(): flags.append("en")
        if not flags: flags = ["id"]
        self.result = {
            "title": title,
            "link": self.e_link.get().strip(),
            "dayStr": self.e_day.get().strip() or "TBA",
            "month": MONTHS.index(self.om_month.get()) + 1,
            "year": int(self.om_year.get()),
            "flags": flags,
        }
        self.destroy()

# ── Main App ──────────────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📚 Manga Admin")
        self.geometry("900x640")
        self.minsize(700, 500)
        self.configure(fg_color=BG)

        self.html_path = DEFAULT_HTML
        self.data = []
        self.selected_id = None

        self._build_ui()
        self._load()

    def _build_ui(self):
        # ── TOP BAR ──
        top = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=60)
        top.pack(fill="x")
        top.pack_propagate(False)

        ctk.CTkLabel(top, text="📚  MANGA ADMIN", font=("Bebas Neue", 26),
                     text_color=ACCENT).pack(side="left", padx=20)

        # File picker
        self.lbl_file = ctk.CTkLabel(top, text=self._short_path(self.html_path),
                                      font=("Space Mono", 10), text_color=TEXT_DIM)
        self.lbl_file.pack(side="left", padx=6)
        ctk.CTkButton(top, text="Ganti File", width=90, height=30,
                      fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT_DIM,
                      font=("Space Mono", 10), command=self._pick_file).pack(side="left", padx=4)

        # Push button
        self.btn_push = ctk.CTkButton(top, text="⬆  PUSH KE GITHUB", width=160, height=36,
                                       fg_color="#2a6aad", hover_color="#1e5090",
                                       text_color="white", font=("Space Mono", 12, "bold"),
                                       command=self._push)
        self.btn_push.pack(side="right", padx=20)

        # Save HTML
        ctk.CTkButton(top, text="💾 SIMPAN HTML", width=140, height=36,
                      fg_color=ACCENT, hover_color="#fff875", text_color=BG,
                      font=("Space Mono", 12, "bold"), command=self._save).pack(side="right", padx=6)

        # ── BODY ──
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=12)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        # Action row
        act = ctk.CTkFrame(body, fg_color="transparent")
        act.grid(row=0, column=0, sticky="ew", pady=(0,10))
        ctk.CTkButton(act, text="＋  TAMBAH", width=120, height=34,
                      fg_color=ACCENT, hover_color="#fff875", text_color=BG,
                      font=("Space Mono", 12, "bold"), command=self._add).pack(side="left")
        ctk.CTkButton(act, text="✎  EDIT", width=100, height=34,
                      fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT,
                      font=("Space Mono", 12), command=self._edit).pack(side="left", padx=8)
        ctk.CTkButton(act, text="✕  HAPUS", width=100, height=34,
                      fg_color=SURFACE2, hover_color="#5a1c22", text_color=RED,
                      font=("Space Mono", 12), command=self._delete).pack(side="left")
        self.lbl_count = ctk.CTkLabel(act, text="0 manga", font=("Space Mono", 12),
                                       text_color=TEXT_DIM)
        self.lbl_count.pack(side="right")

        # Table frame
        tbl_frame = ctk.CTkScrollableFrame(body, fg_color=SURFACE, corner_radius=10)
        tbl_frame.grid(row=1, column=0, sticky="nsew")
        tbl_frame.columnconfigure((1,2,3,4,5), weight=1)
        self.tbl_frame = tbl_frame

        # Status bar
        self.lbl_status = ctk.CTkLabel(self, text="", font=("Space Mono", 11),
                                        text_color=GREEN, height=28)
        self.lbl_status.pack(pady=(0,6))

    def _short_path(self, p):
        parts = p.replace("\\","/").split("/")
        return "/".join(parts[-3:]) if len(parts)>3 else p

    def _pick_file(self):
        p = filedialog.askopenfilename(title="Pilih index.html",
                                        filetypes=[("HTML","*.html"),("All","*.*")],
                                        initialdir=SCRIPT_DIR)
        if p:
            self.html_path = p
            self.lbl_file.configure(text=self._short_path(p))
            self._load()

    def _load(self):
        if os.path.exists(self.html_path):
            self.data = load_from_html(self.html_path)
        else:
            self.data = []
        self._render_table()
        self._status(f"Loaded {len(self.data)} manga dari {os.path.basename(self.html_path)}")

    def _render_table(self):
        for w in self.tbl_frame.winfo_children():
            w.destroy()

        headers = ["#", "Judul", "Tanggal", "Flag", "Link", "Aksi"]
        widths   = [30, 300, 110, 80, 160, 80]
        for c,(h,w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(self.tbl_frame, text=h, font=("Space Mono", 10, "bold"),
                         text_color=TEXT_DIM, width=w, anchor="w").grid(
                row=0, column=c, padx=(4,8), pady=(4,8), sticky="w")

        self.lbl_count.configure(text=f"{len(self.data)} manga")

        sorted_data = sorted(self.data, key=lambda m: self._approx_ts(m))
        for i, m in enumerate(sorted_data):
            row = i + 1
            bg = SURFACE if i%2==0 else SURFACE2

            day = m.get("dayStr","?")
            mo  = MONTHS_SHORT[m.get("month",1)-1]
            yr  = m.get("year","?")
            date_str = f"{day} {mo} {yr}"
            flags_str = " ".join(["IDN" if f=="id" else "ENG" for f in m.get("flags",["id"])])
            link_short = (m.get("link","") or "—")[:28] + ("…" if len(m.get("link",""))>28 else "")

            ctk.CTkLabel(self.tbl_frame, text=str(row), font=("Space Mono",10),
                         text_color=TEXT_DIM, width=30, fg_color=bg).grid(row=row,column=0,padx=(4,8),pady=2,sticky="w")
            ctk.CTkLabel(self.tbl_frame, text=m.get("title","?"), font=("Noto Sans JP",12),
                         text_color=TEXT, width=300, anchor="w", fg_color=bg).grid(row=row,column=1,padx=(0,8),pady=2,sticky="w")
            ctk.CTkLabel(self.tbl_frame, text=date_str, font=("Space Mono",11),
                         text_color=ACCENT, width=110, fg_color=bg).grid(row=row,column=2,padx=(0,8),pady=2,sticky="w")
            ctk.CTkLabel(self.tbl_frame, text=flags_str, font=("Space Mono",10),
                         text_color=TEXT_DIM, width=80, fg_color=bg).grid(row=row,column=3,padx=(0,8),pady=2,sticky="w")
            ctk.CTkLabel(self.tbl_frame, text=link_short, font=("Space Mono",10),
                         text_color=TEXT_DIM, width=160, anchor="w", fg_color=bg).grid(row=row,column=4,padx=(0,8),pady=2,sticky="w")

            mid = m["id"]
            btn_frame = ctk.CTkFrame(self.tbl_frame, fg_color=bg)
            btn_frame.grid(row=row, column=5, padx=(0,4), pady=2, sticky="w")
            ctk.CTkButton(btn_frame, text="Edit", width=40, height=26,
                          fg_color=SURFACE2, hover_color=BORDER, text_color=TEXT,
                          font=("Space Mono",10),
                          command=lambda _id=mid: self._edit_id(_id)).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="✕", width=28, height=26,
                          fg_color=SURFACE2, hover_color="#5a1c22", text_color=RED,
                          font=("Space Mono",10),
                          command=lambda _id=mid: self._delete_id(_id)).pack(side="left")

    def _approx_ts(self, m):
        try:
            d = int(m.get("dayStr","15"))
        except:
            s = str(m.get("dayStr","")).lower()
            d = 5 if "awal" in s else 26 if "akhir" in s else 15
        return datetime(m.get("year",2026), m.get("month",1), max(1,min(d,28)))

    def _add(self):
        dlg = MangaDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["id"] = gen_id()
            self.data.append(dlg.result)
            self._render_table()
            self._status(f'"{dlg.result["title"]}" ditambahkan')

    def _edit(self):
        # Edit item pertama jika tidak ada seleksi — fallback
        if self.data:
            self._edit_id(self.data[0]["id"])

    def _edit_id(self, mid):
        m = next((x for x in self.data if x["id"]==mid), None)
        if not m: return
        dlg = MangaDialog(self, m)
        self.wait_window(dlg)
        if dlg.result:
            dlg.result["id"] = mid
            idx = next(i for i,x in enumerate(self.data) if x["id"]==mid)
            self.data[idx] = dlg.result
            self._render_table()
            self._status(f'"{dlg.result["title"]}" diupdate')

    def _delete(self):
        if self.data:
            self._delete_id(self.data[0]["id"])

    def _delete_id(self, mid):
        m = next((x for x in self.data if x["id"]==mid), None)
        if not m: return
        if messagebox.askyesno("Hapus", f'Hapus "{m["title"]}"?', parent=self):
            self.data = [x for x in self.data if x["id"]!=mid]
            self._render_table()
            self._status(f'"{m["title"]}" dihapus')

    def _save(self):
        if save_to_html(self.html_path, self.data):
            self._status("✓ HTML disimpan!", GREEN)

    def _push(self):
        if not save_to_html(self.html_path, self.data):
            return
        self._status("Pushing ke GitHub...", TEXT_DIM)
        self.update()
        ok, msg = git_push(self.html_path)
        self._status(("✓ " if ok else "✗ ") + msg, GREEN if ok else RED)

    def _status(self, msg, color=None):
        self.lbl_status.configure(text=msg, text_color=color or GREEN)

# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import customtkinter
    except ImportError:
        import subprocess, sys
        print("Menginstall customtkinter...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
        import customtkinter as ctk

    app = App()
    app.mainloop()
