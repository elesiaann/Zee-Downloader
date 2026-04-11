import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, threading, os, queue, re

# ── DPI ────────────────────────────────────────
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass

# ── THEME ──────────────────────────────────────
BG       = "#f2f4f8"
WHITE    = "#ffffff"
HDR      = "#ffffff"      # light header like ViDD
TOOLBAR  = "#ffffff"      # light toolbar
BORDER   = "#e2e6ef"
ACCENT   = "#0070f3"
A_HOV    = "#005dd1"
A_LITE   = "#e6f0ff"
GREEN    = "#16a34a"
G_LITE   = "#dcfce7"
RED      = "#dc2626"
R_LITE   = "#fee2e2"
YELLOW   = "#d97706"
Y_LITE   = "#fef9c3"
TEXT     = "#1a1a2e"
TEXT2    = "#374151"
TEXT3    = "#9ca3af"
DIVIDER  = "#e8ebf2"      # subtle divider lines

F    = ("Segoe UI", 10)
FSB  = ("Segoe UI Semibold", 10)
FS   = ("Segoe UI", 9)
FM   = ("Consolas", 9)

DEFAULT_PATH = r"D:\VideoGrab"

PLAT_COLORS = {
    "TikTok":    ("#ffffff", "#010101"),
    "YouTube":   ("#ffffff", "#ff0000"),
    "Instagram": ("#ffffff", "#c13584"),
    "Facebook":  ("#ffffff", "#1877f2"),
    "Douyin":    ("#ffffff", "#010101"),
    "Video":     (TEXT3,     "#e5e7eb"),
}

def platform_of(url):
    if "douyin.com" in url: return "Douyin"
    if "tiktok.com"    in url: return "TikTok"
    if "youtube.com"   in url or "youtu.be" in url: return "YouTube"
    if "instagram.com" in url: return "Instagram"
    if "facebook.com"  in url or "fb.watch" in url: return "Facebook"
    return "Video"

def is_profile(url):
    # TikTok profile
    if "tiktok.com/@"   in url and "/video/"  not in url: return True
    # YouTube channel
    if "youtube.com/@"  in url and "watch"    not in url: return True
    if "youtube.com/channel/" in url and "watch" not in url: return True
    if "/videos" in url and "youtube.com" in url: return True
    # Instagram profile
    if "instagram.com/" in url and "/p/"      not in url and "/reel/" not in url:
        # Make sure it's not a direct reel/post URL
        parts = url.split("instagram.com/")[-1].strip("/").split("/")
        if len(parts) >= 1 and parts[0] not in ["p", "reel", "reels", "stories"]:
            return True
    # Facebook profile/reels
    if "facebook.com/"  in url and "/reel/"   not in url and "facebook.com/reel" not in url:
        if "/reels" in url or "/videos" in url:
            return True
    # Douyin profile
    if "douyin.com/user/" in url: return True
    return False

# ─────────────────────────────────────────────
#  GLOSSY BUTTON
# ─────────────────────────────────────────────
BTN_STYLES = {
    # top_shine, main_bg, fg, hover_bg, border
    "add":      ("#3b82f6", "#2563eb", "#ffffff", "#1d4ed8", "#1e40af"),
    "start":    ("#22c55e", "#16a34a", "#ffffff", "#15803d", "#166534"),
    "pause":    ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
    "resume":   ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
    "restart":  ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
    "settings": ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
    "stop":     ("#f8fafc", "#f1f5f9", "#dc2626", "#fee2e2", "#fca5a5"),
    "update":   ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
    "ok":       ("#3b82f6", "#2563eb", "#ffffff", "#1d4ed8", "#1e40af"),
    "cancel":   ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
    "apply":    ("#22c55e", "#16a34a", "#ffffff", "#15803d", "#166534"),
    "default":  ("#f8fafc", "#f1f5f9", "#374151", "#e2e8f0", "#cbd5e1"),
}

class Btn(tk.Frame):
    def __init__(self, parent, text="", cmd=None, kind="default", bw=None, **kw):
        super().__init__(parent, cursor="hand2", **kw)
        st = BTN_STYLES.get(kind, BTN_STYLES["default"])
        self._top, self._bot, self._fg, self._htop, self._bc = st
        self._cmd = cmd
        self._on  = True

        def _lgt(c, t=0.55):
            r,g,b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
            return f"#{min(255,int(r+(255-r)*t)):02x}{min(255,int(g+(255-g)*t)):02x}{min(255,int(b+(255-b)*t)):02x}"
        def _drk(c, t=0.28):
            r,g,b = int(c[1:3],16), int(c[3:5],16), int(c[5:7],16)
            return f"#{max(0,int(r*(1-t))):02x}{max(0,int(g*(1-t))):02x}{max(0,int(b*(1-t))):02x}"

        self.configure(bg=self._bc, highlightbackground=self._bc,
                       highlightthickness=1)
        self._shine  = tk.Frame(self, bg=_lgt(self._top), height=3)
        self._shine.pack(fill="x", side="top")
        self._lbl    = tk.Label(self, text=text, font=("Segoe UI Semibold", 9),
                                fg=self._fg, bg=self._bot, padx=14, pady=7)
        if bw: self._lbl.configure(width=bw)
        self._lbl.pack(fill="x")
        self._shadow = tk.Frame(self, bg=_drk(self._bot), height=2)
        self._shadow.pack(fill="x", side="bottom")

        self._lgt = _lgt
        for w in (self, self._shine, self._lbl, self._shadow):
            w.bind("<Enter>",    self._enter)
            w.bind("<Leave>",    self._leave)
            w.bind("<Button-1>", self._click)

    def _enter(self, e):
        if not self._on: return
        self._lbl.configure(bg=self._lgt(self._bot, 0.12))
        self._shine.configure(bg=self._lgt(self._htop, 0.3))

    def _leave(self, e):
        self._lbl.configure(bg=self._bot)
        self._shine.configure(bg=self._lgt(self._top))

    def _click(self, e=None):
        if self._on and self._cmd: self.after(60, self._cmd)

    def set_enabled(self, on):
        self._on = on
        self._lbl.configure(fg=self._fg if on else TEXT3)

    def set_text(self, t): self._lbl.configure(text=t)

# ─────────────────────────────────────────────
#  CARD
# ─────────────────────────────────────────────
class Card(tk.Frame):
    def __init__(self, p, **kw):
        super().__init__(p, bg=WHITE, highlightbackground=BORDER,
                         highlightthickness=1, **kw)

# ─────────────────────────────────────────────
#  TABLE LAYOUT  (grid-based for pixel alignment)
#  Name col = weight 2, all fixed cols = weight 1
#  So Name is always exactly 2x any fixed column
# ─────────────────────────────────────────────
# Fixed column pixel widths (uniform)
COL_FIXED = 110   # Host, Size, Status, Speed, Save to all same width

COLS = [
    ("Name",    0, 0,         True,  "w"),
    ("Host",    1, COL_FIXED, False, "center"),
    ("Size",    2, COL_FIXED, False, "center"),
    ("Status",  3, COL_FIXED, False, "center"),
    ("Speed",   4, COL_FIXED, False, "center"),
    ("Save to", 5, COL_FIXED, False, "w"),
]

def make_table_header(parent):
    bg  = "#e8ecf4"
    bdr = "#c8d0de"
    hdr = tk.Frame(parent, bg=bg, highlightbackground=bdr, highlightthickness=1)
    # Name col weight=2, all fixed cols weight=1 → Name always 2× fixed cols
    hdr.grid_columnconfigure(0, weight=2, minsize=COL_FIXED*2, uniform="col")
    for i in range(1, 6):
        hdr.grid_columnconfigure(i, weight=1, minsize=COL_FIXED, uniform="col")
    for label, col, w, stretch, anchor in COLS:
        cell = tk.Frame(hdr, bg=bg, highlightbackground=bdr, highlightthickness=1)
        cell.grid(row=0, column=col, sticky="nsew")
        if not stretch:
            cell.grid_propagate(False)
        lbl = tk.Label(cell, text=label, font=("Segoe UI Semibold", 9),
                       fg="#1e293b", bg=bg, pady=6, padx=8, anchor=anchor)
        lbl.pack(fill="x")
    return hdr

def _draw_platform_logo(canvas, plat):
    """Draw platform logo — TikTok uses official SVG path scaled to 28x28"""
    canvas.delete("all")
    bg = canvas["bg"]
    if plat == "TikTok" or plat == "Douyin":
        # Official TikTok SVG path scaled 16→28 (factor ~1.75)
        s = 1.75  # scale factor
        def sx(x): return x * s
        def sy(y): return y * s + 1

        # Main black shape (the d-note / TikTok icon)
        canvas.create_rectangle(sx(9),sy(0), sx(10.98),sy(11),
                                 fill="#010101", outline="")
        canvas.create_polygon(
            sx(9),sy(0),  sx(10.98),sy(0),
            sx(12.2),sy(2.5), sx(13.5),sy(3.8), sx(15),sy(4),
            sx(15),sy(6),
            sx(13.3),sy(6), sx(12),sy(5.3), sx(11),sy(4.2),
            sx(11),sy(11),
            sx(9),sy(11),
            fill="#010101", outline="", smooth=True
        )
        cx, cy, r = sx(6), sy(11), sx(5)
        canvas.create_oval(cx-r,cy-r,cx+r,cy+r, fill="#010101", outline="")
        r2 = sx(3)
        canvas.create_oval(cx-r2,cy-r2,cx+r2,cy+r2, fill=bg, outline="")
    elif plat == "YouTube":
        canvas.create_rectangle(1,6,27,22, fill="#ff0000", outline="")
        canvas.create_polygon(11,9, 11,19, 21,14, fill="white")
    elif plat == "Instagram":
        canvas.create_rectangle(2,2,26,26, fill="#e1306c", outline="")
        canvas.create_rectangle(2,2,26,14, fill="#f77737", outline="")
        canvas.create_oval(7,7,21,21, outline="white", width=2, fill="")
        canvas.create_oval(19,6,23,10, fill="white", outline="")
    elif plat == "Facebook":
        canvas.create_rectangle(1,1,27,27, fill="#1877f2", outline="")
        canvas.create_text(14,15, text="f",
                           font=("Georgia", 14, "bold"),
                           fill="white", anchor="center")
    else:
        canvas.create_oval(2,2,26,26, fill="#e5e7eb", outline="#d1d5db")
        canvas.create_text(14,14, text="▶",
                           font=("Segoe UI",9), fill=TEXT3, anchor="center")

# ─────────────────────────────────────────────
#  DOWNLOAD ROW  (table style, JDownloader-inspired)
# ─────────────────────────────────────────────
_row_counter = [0]

class DLRow(tk.Frame):
    def __init__(self, parent, title, url, idx, save_path=""):
        _row_counter[0] += 1
        bg = WHITE if _row_counter[0] % 2 == 0 else "#f7f9fc"
        super().__init__(parent, bg=bg,
                         highlightbackground="#e2e6ef", highlightthickness=1)
        self.url       = url
        self.title     = title
        self.status    = "Waiting"
        self._bg       = bg
        self._save     = save_path
        self._build(idx)

    def _build(self, idx):
        bg  = self._bg
        bdr = "#e2e6ef"
        HDR_BG = "#e8ecf4"

        # Exact match with header: Name=weight 2, fixed cols=weight 1
        self.grid_columnconfigure(0, weight=2, minsize=COL_FIXED*2, uniform="col")
        for i in range(1, 6):
            self.grid_columnconfigure(i, weight=1, minsize=COL_FIXED, uniform="col")

        # ── Col 0: Name (auto-truncates with … when too wide) ──
        c0 = tk.Frame(self, bg=bg, highlightbackground=bdr, highlightthickness=1)
        c0.grid(row=0, column=0, sticky="nsew")
        ni = tk.Frame(c0, bg=bg)
        ni.pack(fill="both", expand=True, padx=(8,4))
        tk.Label(ni, text="⊞", font=("Segoe UI",9),
                 fg="#94a3b8", bg=bg).pack(side="left", padx=(0,5))
        self._name_lbl = tk.Label(ni, text=self.title,
                                   font=("Segoe UI", 9), fg=TEXT,
                                   bg=bg, anchor="w")
        self._name_lbl.pack(side="left", fill="x", expand=True)
        c0.bind("<Configure>", self._on_name_resize)
        self._name_col = c0

        # ── Col 1: Host (platform logo) ──
        c1 = tk.Frame(self, bg=bg, width=COL_FIXED,
                      highlightbackground=bdr, highlightthickness=1)
        c1.grid(row=0, column=1, sticky="nsew")
        c1.grid_propagate(False)
        plat = platform_of(self.url)
        lc = tk.Canvas(c1, width=28, height=28,
                       bg=bg, bd=0, highlightthickness=0)
        lc.place(relx=0.5, rely=0.5, anchor="center")
        _draw_platform_logo(lc, plat)

        # ── Col 2: Size ──
        c2 = tk.Frame(self, bg=bg, width=COL_FIXED,
                      highlightbackground=bdr, highlightthickness=1)
        c2.grid(row=0, column=2, sticky="nsew")
        c2.grid_propagate(False)
        self._size_lbl = tk.Label(c2, text="—",
                                   font=("Segoe UI", 9), fg=TEXT2, bg=bg)
        self._size_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # ── Col 3: Status ──
        c3 = tk.Frame(self, bg=bg, width=COL_FIXED,
                      highlightbackground=bdr, highlightthickness=1)
        c3.grid(row=0, column=3, sticky="nsew")
        c3.grid_propagate(False)
        self._stat_lbl = tk.Label(c3, text="Waiting",
                                   font=("Segoe UI Semibold", 9),
                                   fg=TEXT3, bg=bg)
        self._stat_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # ── Col 4: Speed ──
        c4 = tk.Frame(self, bg=bg, width=COL_FIXED,
                      highlightbackground=bdr, highlightthickness=1)
        c4.grid(row=0, column=4, sticky="nsew")
        c4.grid_propagate(False)
        self._spd_lbl = tk.Label(c4, text="—",
                                  font=("Segoe UI", 9), fg=TEXT2, bg=bg)
        self._spd_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # ── Col 5: Save To ──
        c5 = tk.Frame(self, bg=bg, width=COL_FIXED,
                      highlightbackground=bdr, highlightthickness=1)
        c5.grid(row=0, column=5, sticky="nsew")
        c5.grid_propagate(False)
        self._save_lbl = tk.Label(c5, text=self._save,
                                   font=("Segoe UI", 8), fg=TEXT3,
                                   bg=bg, anchor="w", padx=6)
        self._save_lbl.place(relx=0, rely=0.5, anchor="w")
        c5.bind("<Configure>", self._on_save_resize)
        self._save_col = c5

        # Fixed row height — prevents double-row display bug
        self.configure(height=34)
        self.grid_propagate(False)
        self.pack_propagate(False)

    def _truncate(self, label, full_text, available_px, font=("Segoe UI",9)):
        """Truncate text to fit available_px width, adding … if needed"""
        if available_px <= 20: return
        import tkinter.font as tkfont
        f = tkfont.Font(family=font[0], size=font[1])
        if f.measure(full_text) <= available_px:
            label.configure(text=full_text)
            return
        for i in range(len(full_text), 0, -1):
            t = full_text[:i] + "…"
            if f.measure(t) <= available_px:
                label.configure(text=t)
                return
        label.configure(text="…")

    def _on_name_resize(self, event):
        avail = event.width - 46  # subtract icon + padding
        if avail > 20:
            self._truncate(self._name_lbl, self.title, avail)

    def _on_save_resize(self, event):
        avail = event.width - 12
        if avail > 20:
            self._truncate(self._save_lbl, self._save, avail, ("Segoe UI",8))

    def set_status(self, s):
        self.status = s
        cfgs = {
            "Waiting":     ("Waiting",        TEXT3,  self._bg),
            "extracting":  ("🔍 Extracting",  ACCENT, self._bg),
            "downloading": ("⬇ Downloading",  ACCENT, self._bg),
            "done":        ("✓ Finished",      GREEN,  self._bg),
            "failed":      ("✕ Failed",         RED,    self._bg),
            "stopped":     ("⏹ Stopped",       YELLOW, self._bg),
        }
        txt, fg, bg = cfgs.get(s, ("?", TEXT3, self._bg))
        self._stat_lbl.configure(text=txt, fg=fg)
        # Clear speed when done/waiting
        if s in ("done", "Waiting", "extracting", "stopped"):
            self._spd_lbl.configure(text="—", fg=TEXT3)

    def set_pct(self, p):
        self._spd_lbl.configure(text=p, fg=ACCENT)

    def set_size(self, s):
        self._size_lbl.configure(text=s, fg=TEXT2)

    def set_speed(self, s):
        self._spd_lbl.configure(text=s, fg=ACCENT)

# ─────────────────────────────────────────────
#  URL DIALOG
# ─────────────────────────────────────────────
class URLDialog(tk.Toplevel):
    def __init__(self, parent, cb):
        super().__init__(parent)
        self.cb = cb
        self.title("Add URLs")
        self.geometry("660x500")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.grab_set()

        # Dark header
        hdr = tk.Frame(self, bg=HDR)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Paste URLs of Videos / Users to Download",
                 font=("Segoe UI Semibold", 12), fg=TEXT,
                 bg=HDR).pack(padx=20, pady=14)

        # Footer FIRST so it always shows
        footer = tk.Frame(self, bg=WHITE,
                          highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x", side="bottom")
        Btn(footer, text="Cancel", kind="cancel", bw=14,
            cmd=self.destroy).pack(side="left", padx=16, pady=10)
        Btn(footer, text="OK", kind="ok", bw=14,
            cmd=self._ok).pack(side="right", padx=16, pady=10)

        # Body
        body = tk.Frame(self, bg=BG, padx=16, pady=10)
        body.pack(fill="both", expand=True)

        tk.Label(body, text="Download URLs  (one per line)",
                 font=FSB, fg=TEXT2, bg=BG).pack(anchor="w", pady=(0,4))

        url_card = Card(body)
        url_card.pack(fill="both", expand=True, pady=(0,8))

        self._ph = (
            "Example Input Formats\n\n"
            "TikTok\n"
            "https://www.tiktok.com/@username  →  All User Videos\n"
            "https://www.tiktok.com/@user/video/ID  →  Single Video\n\n"
            "YouTube\n"
            "https://www.youtube.com/@Channel/videos  →  All Videos\n"
            "https://www.youtube.com/watch?v=ID  →  Single Video\n\n"
            "Instagram\n"
            "https://www.instagram.com/username  →  All Reels\n"
            "https://www.instagram.com/reel/ID  →  Single Reel\n\n"
            "Facebook\n"
            "https://www.facebook.com/username/reels  →  All Reels\n\n"
            "Douyin\n"
            "https://www.douyin.com/user/ID  →  All Videos"
        )
        self._box = tk.Text(url_card, font=F, fg=TEXT3, bg=WHITE,
                            bd=0, relief="flat", padx=12, pady=10,
                            wrap="none", insertbackground=TEXT)
        self._box.insert("1.0", self._ph)
        self._box.pack(fill="both", expand=True)
        self._box.bind("<FocusIn>", self._clear)

        tk.Label(body, text="Ignore List",
                 font=FSB, fg=TEXT2, bg=BG).pack(anchor="w", pady=(0,4))
        ig = Card(body); ig.pack(fill="x")
        self._ig = tk.Text(ig, font=FS, fg=TEXT3, bg=WHITE,
                           bd=0, relief="flat", padx=12, pady=6,
                           height=3, wrap="none")
        self._ig.insert("1.0", "Ignore list will be here")
        self._ig.pack(fill="x")

    def _clear(self, e):
        if self._box.get("1.0", "end").strip().startswith("Example"):
            self._box.delete("1.0", "end")
            self._box.configure(fg=TEXT)

    def _ok(self):
        raw  = self._box.get("1.0", "end").strip()
        urls = [u.strip() for u in raw.splitlines()
                if u.strip() and not u.strip().startswith("Example")]
        if not urls:
            messagebox.showwarning("Zee Downloader", "Enter at least one URL.", parent=self)
            return
        self.cb(urls)
        self.destroy()

# ─────────────────────────────────────────────
#  SETTINGS DIALOG
# ─────────────────────────────────────────────
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, cfg, on_save):
        super().__init__(parent)
        self.on_save = on_save; self.s = cfg
        self.title("Settings")
        self.geometry("600x540")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()

        self._tabs = []; self._active = "tool"
        tab_bar = tk.Frame(self, bg=HDR)
        tab_bar.pack(fill="x")
        for lbl, val in [("⚙  Tool Settings", "tool"),
                          ("🌐  Platform Settings", "platform")]:
            b = tk.Label(tab_bar, text=lbl, font=FSB,
                         fg=TEXT if val == "tool" else TEXT3,
                         bg=HDR if val == "tool" else TOOLBAR,
                         padx=22, pady=12, cursor="hand2")
            b.pack(side="left")
            b.bind("<Button-1>", lambda e, v=val: self._sw(v))
            self._tabs.append((b, val))

        self._content = tk.Frame(self, bg=BG)
        self._content.pack(fill="both", expand=True)
        self._pages = {"tool": self._tool(), "platform": self._plat()}
        self._sw("tool")

        footer = tk.Frame(self, bg=WHITE,
                          highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x", side="bottom")
        Btn(footer, text="Discard", kind="cancel",
            cmd=self.destroy).pack(side="right", padx=(6, 16), pady=10)
        Btn(footer, text="Apply", kind="apply",
            cmd=self._apply).pack(side="right", pady=10)

    def _sw(self, val):
        for b, v in self._tabs:
            b.configure(fg=TEXT if v == val else TEXT3,
                        bg=HDR if v == val else TOOLBAR)
        for p in self._pages.values(): p.pack_forget()
        self._pages[val].pack(fill="both", expand=True, padx=20, pady=16)

    def _sec(self, p, t):
        f = tk.Frame(p, bg=WHITE)
        tk.Label(f, text=t, font=("Segoe UI Semibold", 9),
                 fg=ACCENT, bg=WHITE).pack(anchor="w", pady=(0,3))
        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", pady=(0,8))
        return f

    def _row(self, p, lbl, fn):
        r = tk.Frame(p, bg=WHITE); r.pack(fill="x", pady=4)
        tk.Label(r, text=lbl, font=F, fg=TEXT2,
                 bg=WHITE, width=28, anchor="w").pack(side="left")
        fn(r); return r

    def _cb(self, p, var, vals, w=10):
        ttk.Combobox(p, textvariable=var, values=vals,
                     width=w, state="readonly", font=F).pack(side="left", padx=6)

    def _tool(self):
        outer = tk.Frame(self._content, bg=BG)
        card  = Card(outer); card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=WHITE, padx=20, pady=14)
        inner.pack(fill="both", expand=True)

        s1 = self._sec(inner, "Threads Setting"); s1.pack(fill="x", pady=(0,10))
        self.v_thr = tk.StringVar(value=self.s.get("threads", "2"))
        self._row(s1, "Simultaneous Downloads:",
                  lambda p: self._cb(p, self.v_thr, ["1","2","3","4","5"], 6))

        s2 = self._sec(inner, "Download Settings"); s2.pack(fill="x", pady=(0,10))
        self.v_lim = tk.StringVar(value=self.s.get("limit",  "1000"))
        self.v_fmt = tk.StringVar(value=self.s.get("format", "MP4"))
        self.v_vc  = tk.StringVar(value=self.s.get("vcodec", "H.264"))
        self.v_ac  = tk.StringVar(value=self.s.get("acodec", "AAC"))
        self._row(s2, "Video Limit (per profile):",
                  lambda p: self._cb(p, self.v_lim, ["50","100","250","500","1000","All"], 8))
        self._row(s2, "Output Format:",
                  lambda p: self._cb(p, self.v_fmt, ["MP4","MKV","WEBM","MP3","M4A"], 8))
        self._row(s2, "Preferred Video Codec:",
                  lambda p: self._cb(p, self.v_vc,  ["H.264","H.265","AV1","VP9","Any"], 8))
        self._row(s2, "Preferred Audio Codec:",
                  lambda p: self._cb(p, self.v_ac,  ["AAC","MP3","Opus","Any"], 8))

        s3 = self._sec(inner, "Save Location"); s3.pack(fill="x", pady=(0,10))
        self.v_path = tk.StringVar(value=self.s.get("path", DEFAULT_PATH))
        pr = tk.Frame(s3, bg=WHITE); pr.pack(fill="x", pady=(0,6))
        tk.Label(pr, text="Save Path:", font=F, fg=TEXT2,
                 bg=WHITE, width=28, anchor="w").pack(side="left")
        path_entry = tk.Entry(pr, textvariable=self.v_path, font=FM,
                              fg=TEXT, bg=BG, bd=0, relief="flat",
                              highlightbackground=BORDER, highlightthickness=1,
                              width=26, cursor="hand2")
        path_entry.pack(side="left", ipady=5, padx=(6,6))
        path_entry.bind("<Button-1>", lambda e: self._browse())
        Btn(pr, text="Browse", kind="default", cmd=self._browse).pack(side="left")

        s4 = self._sec(inner, "Options"); s4.pack(fill="x")
        self.v_thumb = tk.BooleanVar(value=self.s.get("embed_thumb", True))
        self.v_meta  = tk.BooleanVar(value=self.s.get("embed_meta",  True))
        self.v_audio = tk.BooleanVar(value=self.s.get("audio_only",  False))
        for var, lbl in [(self.v_thumb, "Embed Thumbnail"),
                         (self.v_meta,  "Embed Metadata"),
                         (self.v_audio, "Audio Only")]:
            tk.Checkbutton(s4, text=lbl, variable=var, font=F,
                           fg=TEXT2, bg=WHITE, selectcolor=WHITE,
                           activebackground=WHITE).pack(anchor="w", pady=2)
        return outer

    def _plat(self):
        outer = tk.Frame(self._content, bg=BG)
        card  = Card(outer); card.pack(fill="both", expand=True)
        inner = tk.Frame(card, bg=WHITE, padx=20, pady=14)
        inner.pack(fill="both", expand=True)
        self._sec(inner, "Supported URL Formats").pack(fill="x")
        for plat, rows in [
            ("TikTok",    [("All videos",  "tiktok.com/@username"),
                           ("Single video","tiktok.com/@user/video/ID")]),
            ("YouTube",   [("All videos",  "youtube.com/@Channel/videos"),
                           ("Single video","youtube.com/watch?v=ID")]),
            ("Instagram", [("All reels",   "instagram.com/username"),
                           ("Single reel", "instagram.com/reel/ID")]),
            ("Facebook",  [("All reels",   "facebook.com/username/reels")]),
            ("Douyin",    [("All videos",  "douyin.com/user/ID")]),
        ]:
            row = tk.Frame(inner, bg="#f8faff",
                           highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", pady=3)
            pfg, pbg = PLAT_COLORS[plat]
            tk.Label(row, text=f" {plat} ", font=("Segoe UI Semibold", 9),
                     fg=pfg, bg=pbg, padx=8, pady=6).pack(side="left", padx=(0,10))
            col = tk.Frame(row, bg="#f8faff")
            col.pack(side="left", fill="x", expand=True, pady=4)
            for desc, url in rows:
                tk.Label(col, text=f"{desc}:  {url}", font=FM,
                         fg=TEXT2, bg="#f8faff", anchor="w").pack(anchor="w")
        return outer

    def _browse(self):
        p = filedialog.askdirectory(initialdir=self.v_path.get())
        if p: self.v_path.set(p)

    def _apply(self):
        self.on_save({
            "threads":     self.v_thr.get(),
            "limit":       self.v_lim.get(),
            "format":      self.v_fmt.get(),
            "vcodec":      self.v_vc.get(),
            "acodec":      self.v_ac.get(),
            "path":        self.v_path.get(),
            "embed_thumb": self.v_thumb.get(),
            "embed_meta":  self.v_meta.get(),
            "audio_only":  self.v_audio.get(),
        })
        self.destroy()

# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class VideoGrab(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zee Downloader")
        self.geometry("960x640")
        self.minsize(820, 540)
        self.configure(bg=BG)

        self.cfg = {
            "threads":"2", "limit":"1000", "format":"MP4",
            "vcodec":"H.264", "acodec":"AAC", "path":DEFAULT_PATH,
            "embed_thumb":True, "embed_meta":True, "audio_only":False,
        }
        self.q          = queue.Queue()
        self.rows       = []
        self.ok_count   = 0
        self.fail_count = 0
        
        # ── FIXED: Proper process and thread management ──
        self._stop_flag = threading.Event()      # Signal to stop downloads
        self._processes = []                      # Track all running processes
        self._processes_lock = threading.Lock()   # Thread-safe process list
        self._extract_processes = []              # Track extraction processes
        self._is_downloading = False              # Track if downloads are running
        self._is_paused = False                   # Track pause state

        self._styles()
        self._build()
        self._poll()

    def _styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("DL.Horizontal.TProgressbar",
                    troughcolor=BORDER, background=ACCENT,
                    lightcolor="#7fb3ff", darkcolor=A_HOV,
                    bordercolor=WHITE, thickness=3)
        s.configure("TCombobox", fieldbackground=BG, background=BG,
                    foreground=TEXT, selectforeground=TEXT,
                    selectbackground=A_LITE, arrowcolor=TEXT2,
                    bordercolor=BORDER)
        s.map("TCombobox",
              fieldbackground=[("readonly", BG)],
              foreground=[("readonly", TEXT)])

    def _build(self):
        # ── TITLE BAR (ViDD-style: light, logo + name) ──
        title_bar = tk.Frame(self, bg=WHITE,
                             highlightbackground=BORDER, highlightthickness=1)
        title_bar.pack(fill="x")

        lc = tk.Canvas(title_bar, width=40, height=40,
                       bg=WHITE, bd=0, highlightthickness=0)
        lc.pack(side="left", padx=(14,6), pady=8)
        # Outer circle
        lc.create_oval(1,1,39,39, fill="#0070f3", outline="#0070f3")
        # Shine arc
        lc.create_arc(4,4,36,22, start=0, extent=180,
                      fill="#60a5fa", outline="", style="chord")
        # Z letter
        lc.create_line(10,12,30,12, fill="white", width=2.8, capstyle="round")
        lc.create_line(30,12,10,28, fill="white", width=2.2, capstyle="round")
        lc.create_line(10,28,30,28, fill="white", width=2.8, capstyle="round")
        # V subscript
        lc.create_line(20,31,24,38, fill="#93c5fd", width=1.5, capstyle="round")
        lc.create_line(24,38,28,31, fill="#93c5fd", width=1.5, capstyle="round")

        tf = tk.Frame(title_bar, bg=WHITE)
        tf.pack(side="left", pady=8)
        tk.Label(tf, text="Zee Downloader",
                 font=("Segoe UI Semibold",13), fg=TEXT,
                 bg=WHITE).pack(anchor="w")
        tk.Label(tf, text="Advanced Video Downloader  •  yt-dlp",
                 font=("Segoe UI",8), fg=TEXT3, bg=WHITE).pack(anchor="w")

        # ── TOOLBAR (ViDD-style: all buttons in one row, light bg) ──
        tb = tk.Frame(self, bg=WHITE,
                      highlightbackground=BORDER, highlightthickness=1)
        tb.pack(fill="x")

        btn_row = tk.Frame(tb, bg=WHITE)
        btn_row.pack(side="left", padx=10, pady=8)

        Btn(btn_row, text="＋  Add URL",  kind="add",      bw=12, cmd=self._add_url ).pack(side="left", padx=(0,3))
        Btn(btn_row, text="▶  Start",    kind="start",    bw=9,  cmd=self._start   ).pack(side="left", padx=(0,3))
        self._pause_btn = Btn(btn_row, text="⏸  Pause",   kind="pause",    bw=9,  cmd=self._pause   )
        self._pause_btn.pack(side="left", padx=(0,3))
        Btn(btn_row, text="↺  Restart", kind="restart",  bw=9,  cmd=self._restart ).pack(side="left", padx=(0,3))
        Btn(btn_row, text="⚙  Settings",kind="settings", bw=9,  cmd=self._settings).pack(side="left", padx=(0,3))

        # Stats badges right of toolbar
        sf = tk.Frame(tb, bg=WHITE)
        sf.pack(side="right", padx=12)
        for val, border, fg, attr in [
            ("0", BORDER, TEXT2, "_s_total"),
            ("0", GREEN,  GREEN, "_s_ok"),
            ("0", RED,    RED,   "_s_fail"),
        ]:
            f = tk.Frame(sf, bg=WHITE,
                         highlightbackground=border, highlightthickness=1)
            f.pack(side="left", padx=3)
            lw = tk.Label(f, text=val, font=("Segoe UI Semibold",12),
                          fg=fg, bg=WHITE, width=4, pady=5)
            lw.pack()
            setattr(self, attr, lw)

        # ── BODY ──
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Sub-header row
        sh = tk.Frame(body, bg=BG)
        sh.pack(fill="x", padx=14, pady=(10,6))
        tk.Label(sh, text="Downloads", font=("Segoe UI Semibold",12),
                 fg=TEXT, bg=BG).pack(side="left")

        Btn(sh, text="Update", kind="update", bw=8,
            cmd=self._update).pack(side="right", padx=(6,0))
        tk.Button(sh, text="Clear All", font=FS,
                  fg=RED, bg=BG, bd=0, cursor="hand2",
                  activebackground=BG, activeforeground=RED,
                  command=self._clear).pack(side="right", padx=(0,8))
        self._prog_lbl = tk.Label(sh, text="", font=("Segoe UI Semibold",10),
                                   fg=GREEN, bg=BG)
        self._prog_lbl.pack(side="right", padx=(0,12))

        # ── SCROLLABLE DOWNLOAD LIST ──
        list_card = Card(body)
        list_card.pack(fill="both", expand=True, padx=14, pady=(0,8))

        # Table column header
        make_table_header(list_card).pack(fill="x")

        self._canvas = tk.Canvas(list_card, bg=WHITE, bd=0, highlightthickness=0)
        vsb = ttk.Scrollbar(list_card, orient="vertical", command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas, bg=WHITE)
        self._inner.bind("<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))
        self._cw = self._canvas.create_window((0,0), window=self._inner, anchor="nw")
        self._canvas.bind("<Configure>",
            lambda e: self._canvas.itemconfig(self._cw, width=e.width))
        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._empty = tk.Label(self._inner,
                               text="No downloads yet\n\nClick  ＋ Add URL  to get started",
                               font=("Segoe UI",12), fg=TEXT3,
                               bg=WHITE, justify="center")
        self._empty.pack(expand=True, pady=100)

        # ── STATUS BAR ──
        sb = tk.Frame(self, bg=WHITE,
                      highlightbackground=BORDER, highlightthickness=1)
        sb.pack(fill="x", side="bottom")
        self._status_lbl = tk.Label(sb, text="Ready  •  Zee Downloader v1.0",
                                     font=FS, fg=TEXT3,
                                     bg=WHITE, anchor="w", padx=14, pady=5)
        self._status_lbl.pack(side="left")
        Btn(sb, text="⏹  Stop", kind="stop", bw=8,
            cmd=self._stop).pack(side="right", padx=12, pady=5)
        tk.Label(sb, text="Zee Downloader v1.0", font=("Segoe UI",8),
                 fg=TEXT3, bg=WHITE, padx=12).pack(side="right")

    # ── HELPERS ──────────────────────────────
    def _add_extract_overlay(self, url, username):
        """Show an animated loading card while extracting a profile."""
        if self._empty:
            self._empty.destroy()
            self._empty = None

        card = tk.Frame(self._inner, bg=WHITE,
                        highlightbackground="#c8d0de", highlightthickness=2)
        card.pack(fill="x", pady=2)

        inner = tk.Frame(card, bg=WHITE)
        inner.pack(expand=True, pady=16)

        # Animated dots spinner
        spinner_lbl = tk.Label(inner, text="●  ●  ●",
                               font=("Segoe UI", 14), fg=ACCENT, bg=WHITE)
        spinner_lbl.pack()

        # Username label
        uname = f"@{username}" if username else url[:50]
        tk.Label(inner, text=f"Extracting videos from {uname}",
                 font=("Segoe UI Semibold", 10), fg=TEXT2, bg=WHITE).pack(pady=(6,2))
        tk.Label(inner, text="Please wait — listing videos one by one…",
                 font=("Segoe UI", 9), fg=TEXT3, bg=WHITE).pack()

        # Animate dots
        dots = ["●  ○  ○", "○  ●  ○", "○  ○  ●", "○  ●  ○"]
        card._dot_idx = [0]
        card._active  = [True]

        def animate():
            if not card._active[0]: return
            try:
                card._dot_idx[0] = (card._dot_idx[0] + 1) % len(dots)
                spinner_lbl.configure(text=dots[card._dot_idx[0]])
                spinner_lbl.after(300, animate)
            except Exception:
                pass
        animate()

        # Store ref so we can destroy it later
        card.url       = url
        card.subfolder = username
        card._active   = [True]
        return card

    def _add_row(self, title, url):
        if self._empty:
            self._empty.destroy()
            self._empty = None
        idx = len(self.rows) + 1
        save = self.cfg.get("path", DEFAULT_PATH)
        row  = DLRow(self._inner, title, url, idx, save_path=save)
        row.pack(fill="x", pady=0)
        self.rows.append(row)
        self._s_total.configure(text=str(len(self.rows)))
        return row

    def _set_status(self, msg):
        self._status_lbl.configure(text=msg)

    # ── ACTIONS ──────────────────────────────
    def _add_url(self):   URLDialog(self, self._on_urls)
    def _settings(self):  SettingsDialog(self, self.cfg, self.cfg.update)
    
    def _pause(self):
        """Toggle pause/resume for downloads"""
        if not self._is_downloading:
            self._set_status("No active downloads to pause.")
            return
            
        if self._is_paused:
            # Resume
            self._is_paused = False
            self._stop_flag.clear()
            self._pause_btn.set_text("⏸  Pause")
            self._set_status("▶ Resumed downloads.")
            # Restart pending downloads
            self._start()
        else:
            # Pause - set flag but don't terminate processes
            self._is_paused = True
            self._stop_flag.set()
            self._pause_btn.set_text("▶  Resume")
            self._set_status("⏸ Paused - click Resume to continue.")
            # Mark downloading items as waiting
            for r in self.rows:
                if r.status == "downloading":
                    r.set_status("Waiting")
    
    def _restart(self):
        for r in self.rows:
            if r.status in ("failed", "stopped"):
                r.set_status("Waiting")
        self._start()

    def _on_urls(self, urls):
        for url in urls:
            url = url.strip()
            if not url:
                continue
                
            if is_profile(url):
                # Extract username for subfolder name
                username = ""
                if "@" in url:
                    part = url.split("@")[-1].split("/")[0].split("?")[0]
                    username = part[:40]
                elif "douyin.com/user/" in url:
                    part = url.split("/user/")[-1].split("/")[0].split("?")[0]
                    username = f"douyin_{part[:30]}"
                elif "youtube.com/channel/" in url:
                    part = url.split("/channel/")[-1].split("/")[0].split("?")[0]
                    username = part[:40]
                    
                short = username[:30] if username else url[-30:]
                # Show extraction overlay card instead of a DLRow
                tr = self._add_extract_overlay(url, username)
                self._set_status(f"🔍 Extracting videos from @{short}…")
                threading.Thread(target=self._extract,
                                 args=(url, tr, username), daemon=True).start()
            else:
                # Single video - extract title from URL
                title = self._get_title_from_url(url)
                row = self._add_row(title, url)
                row.subfolder  = None   # no subfolder for single videos
                row.is_profile = False

    def _get_title_from_url(self, url):
        """Extract a readable title from URL"""
        if "/video/" in url:
            return url.split("/video/")[-1].split("?")[0][:40]
        if "watch?v=" in url:
            return url.split("watch?v=")[-1].split("&")[0][:40]
        if "/reel/" in url:
            return url.split("/reel/")[-1].split("?")[0][:40]
        if "/p/" in url:
            return url.split("/p/")[-1].split("?")[0][:40]
        return url[-40:]

    def _get_extractor_args(self, url):
        """Get platform-specific yt-dlp arguments for extraction"""
        plat = platform_of(url)
        args = []
        
        if plat == "TikTok":
            args += [
                "--extractor-args", "tiktok:api_hostname=api22-normal-c-alisg.tiktokv.com",
            ]
        elif plat == "Douyin":
            args += [
                "--extractor-args", "douyin:api_hostname=api.douyin.wtf",
            ]
        elif plat == "Instagram":
            # Instagram needs cookies for some content
            args += [
                "--extractor-args", "instagram:include_ads=False",
            ]
        elif plat == "YouTube":
            args += [
                "--extractor-args", "youtube:skip=dash,hls",
            ]
        elif plat == "Facebook":
            args += [
                "--extractor-args", "facebook:api_hostname=www.facebook.com",
            ]
            
        return args

    def _extract(self, url, placeholder, username=""):
        """Extract video links from profile URL"""
        proc = None
        try:
            lim = self.cfg.get("limit", "1000")
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--print", "%(title)s|||%(webpage_url)s",
                "--no-warnings",
                "--no-check-certificates",
                "--ignore-errors",           # Continue on errors
                "--socket-timeout", "30",    # Timeout for slow connections
            ]
            
            # Add platform-specific args
            cmd += self._get_extractor_args(url)
            
            if lim != "All":
                try:
                    cmd += ["--playlist-end", str(int(lim))]
                except ValueError:
                    pass
                    
            cmd.append(url)

            # Track extraction process
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, 
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            with self._processes_lock:
                self._extract_processes.append(proc)
            
            count = 0
            errors = []
            
            # Read stdout line by line
            for raw_line in iter(proc.stdout.readline, ''):
                if self._stop_flag.is_set():
                    proc.terminate()
                    break
                    
                line = raw_line.strip()
                if not line:
                    continue
                    
                if "|||" not in line:
                    # Might be an error or info message
                    if "ERROR" in line or "error" in line.lower():
                        errors.append(line)
                    continue
                    
                parts = line.split("|||", 1)
                t = parts[0].strip() or "Untitled"
                u = parts[1].strip() if len(parts) > 1 else ""
                
                if u:
                    count += 1
                    # Remove placeholder only after first video found
                    if count == 1:
                        self.q.put(("extract_remove_ph", placeholder, username))
                    self.q.put(("extract_row", t, u, username, count))

            proc.wait()
            
            # If no videos found and placeholder still exists, remove it
            if count == 0:
                self.q.put(("extract_remove_ph", placeholder, username))
                
                # Read stderr for error info
                stderr_output = proc.stderr.read() if proc.stderr else ""
                if stderr_output:
                    errors.append(stderr_output[:200])
                    
                error_msg = "; ".join(errors)[:100] if errors else "Profile may be empty or private"
                self.q.put(("status", f"⚠ No videos found: {error_msg}"))
            else:
                label = f"@{username}" if username else "profile"
                self.q.put(("status", f"✅ {count} videos from {label} — click ▶ Start"))
                
        except FileNotFoundError:
            self.q.put(("extract_remove_ph", placeholder, username))
            self.q.put(("status", "❌ yt-dlp not found! Please install yt-dlp."))
        except Exception as e:
            self.q.put(("extract_remove_ph", placeholder, username))
            self.q.put(("status", f"⚠ Extraction error: {str(e)[:50]}"))
        finally:
            if proc:
                with self._processes_lock:
                    if proc in self._extract_processes:
                        self._extract_processes.remove(proc)

    def _start(self):
        if self._is_paused:
            self._is_paused = False
            self._stop_flag.clear()
            self._pause_btn.set_text("⏸  Pause")
            
        pending = [r for r in self.rows
                   if r.status in ("Waiting", "failed", "stopped") and "🔍" not in str(r.title)]
        if not pending:
            messagebox.showinfo("Zee Downloader", "No queued downloads.\nAdd URLs first.")
            return
            
        self._is_downloading = True
        self._stop_flag.clear()
        threading.Thread(target=self._run, args=(pending,), daemon=True).start()

    def _run(self, rows):
        threads_count = min(int(self.cfg.get("threads", "3")), len(rows))
        sem      = threading.Semaphore(threads_count)
        finished = [0]
        total    = len(rows)
        lock     = threading.Lock()

        def download_one(row):
            if self._stop_flag.is_set():
                return
                
            with sem:
                if self._stop_flag.is_set():
                    self.q.put(("row_status", row, "stopped"))
                    return
                    
                self.q.put(("row_status", row, "downloading"))
                ok = self._exec(
                    self._cmd(row.url, getattr(row, "subfolder", None)), row)
                    
                if self._stop_flag.is_set():
                    self.q.put(("row_status", row, "stopped"))
                else:
                    self.q.put(("row_status", row, "done" if ok else "failed"))
                    self.q.put(("count", ok))
                    
                with lock:
                    finished[0] += 1
                    if not self._stop_flag.is_set():
                        self.q.put(("status", f"Downloading… {finished[0]}/{total} complete"))

        # Launch ALL threads immediately — semaphore limits concurrency
        threads = [threading.Thread(target=download_one, args=(r,), daemon=True)
                   for r in rows]
        for t in threads: t.start()
        for t in threads: t.join()
        
        self._is_downloading = False
        if not self._stop_flag.is_set():
            self.q.put(("done",))

    def _cmd(self, url, subfolder=None):
        s    = self.cfg
        base = s["path"]
        path = os.path.join(base, subfolder) if subfolder else base
        os.makedirs(path, exist_ok=True)
        
        cmd = [
            "yt-dlp", "--no-mtime", "--windows-filenames", "--newline",
            "--paths", path,
            "--output", "%(title,Untitled)s.%(ext)s",
            "--trim-filenames", "180",
            "--socket-timeout", "30",
            "--retries", "3",
            "--fragment-retries", "3",
        ]
        
        plat = platform_of(url)
        
        # Platform-specific options
        if plat == "TikTok":
            cmd += [
                "--extractor-args", "tiktok:api_hostname=api22-normal-c-alisg.tiktokv.com",
                "--concurrent-fragments", "4",
                "--no-check-certificates",
            ]
        elif plat == "Douyin":
            cmd += [
                "--extractor-args", "douyin:api_hostname=api.douyin.wtf",
                "--concurrent-fragments", "4",
                "--no-check-certificates",
            ]
        elif plat == "YouTube":
            cmd += [
                "--concurrent-fragments", "4",
            ]
        elif plat == "Instagram":
            cmd += [
                "--no-check-certificates",
            ]
        elif plat == "Facebook":
            cmd += [
                "--no-check-certificates",
            ]
            
        if s.get("embed_meta"):  
            cmd.append("--embed-metadata")
        if s.get("embed_thumb"):
            cmd += ["--embed-thumbnail", "--convert-thumbnails", "png>png/jpg"]
        if s.get("audio_only"):
            fmt = s["format"].lower() if s["format"] in ["MP3","M4A"] else "mp3"
            cmd += ["-x", "--audio-format", fmt]
        else:
            remux = s["format"].lower() if s["format"] in ["MP4","MKV","WEBM"] else "mp4"
            vc_m  = {"H.264":"h264","H.265":"h265","AV1":"av01","VP9":"vp9","Any":""}
            ac_m  = {"AAC":"aac","MP3":"mp3","Opus":"opus","Any":""}
            vc, ac = vc_m.get(s["vcodec"],""), ac_m.get(s["acodec"],"")
            parts  = []
            if vc: parts.append(f"+vcodec:{vc}")
            parts += ["res:1080", "+quality"]
            if ac: parts.append(f"+acodec:{ac}")
            cmd  += ["--remux-video", remux,
                     "--format", "bestvideo+bestaudio/best",
                     "--format-sort", ",".join(parts)]
        cmd.append(url)
        return cmd

    def _exec(self, cmd, row=None):
        proc = None
        try:
            # Create process with ability to terminate
            creationflags = 0
            if os.name == 'nt':
                creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
                
            proc = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=True, 
                encoding="utf-8", 
                errors="replace",
                creationflags=creationflags
            )
            
            # Track this process
            with self._processes_lock:
                self._processes.append(proc)
            
            for line in iter(proc.stdout.readline, ''):
                # Check stop flag
                if self._stop_flag.is_set():
                    self._terminate_process(proc)
                    return False
                    
                line = line.rstrip()
                if not line: continue

                # yt-dlp progress line format:
                # [download]  45.2% of    2.01MiB at  676.52KiB/s ETA 00:01
                m_pct   = re.search(r'(\d+\.?\d*)%', line)
                m_speed = re.search(r'at\s+(\d+\.?\d*\s*[KMGk]i?B/s)', line)
                m_size  = re.search(r'of\s+~?(\d+\.?\d*\s*[KMGk]i?B)', line)

                if "[download]" in line and m_pct and row:
                    pct = m_pct.group(1) + "%"
                    self.q.put(("row_pct",  row, pct))
                    self.q.put(("prog_lbl", pct))
                if m_speed and row:
                    self.q.put(("row_spd", row, m_speed.group(1)))
                if m_size and row:
                    self.q.put(("row_size", row, m_size.group(1)))

            proc.wait()
            return proc.returncode == 0
            
        except FileNotFoundError:
            self.q.put(("status", "❌ yt-dlp not found! Please install yt-dlp."))
            return False
        except Exception as e:
            self.q.put(("status", f"❌ {e}"))
            return False
        finally:
            if proc:
                with self._processes_lock:
                    if proc in self._processes:
                        self._processes.remove(proc)

    def _terminate_process(self, proc):
        """Safely terminate a process"""
        try:
            if os.name == 'nt':
                # On Windows, use taskkill for process tree
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(proc.pid)],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass

    def _stop(self):
        """Stop all downloads and extractions"""
        self._stop_flag.set()
        self._is_downloading = False
        self._is_paused = False
        self._pause_btn.set_text("⏸  Pause")
        
        # Terminate all running processes
        with self._processes_lock:
            for proc in self._processes[:]:  # Copy list to avoid modification during iteration
                self._terminate_process(proc)
            for proc in self._extract_processes[:]:
                self._terminate_process(proc)
            self._processes.clear()
            self._extract_processes.clear()
        
        # Mark downloading rows as stopped
        for r in self.rows:
            if r.status == "downloading":
                r.set_status("stopped")
                
        self._set_status("⏹ Stopped all downloads.")

    def _clear(self):
        # Stop any running downloads first
        self._stop()
        
        _row_counter[0] = 0
        for r in self.rows: r.destroy()
        self.rows.clear()
        self.ok_count = self.fail_count = 0
        self._s_total.configure(text="0")
        self._s_ok.configure(text="0")
        self._s_fail.configure(text="0")
        self._prog_lbl.configure(text="")
        self._empty = tk.Label(self._inner,
                               text="No downloads yet\n\nClick  ＋ Add URL  to get started",
                               font=("Segoe UI",12), fg=TEXT3,
                               bg=WHITE, justify="center")
        self._empty.pack(expand=True, pady=100)
        self._set_status("Ready  •  Zee Downloader v1.0")

    def _update(self):
        self._set_status("Checking for updates…")
        def run():
            try:
                r = subprocess.run(
                    ["yt-dlp", "--update"],
                    capture_output=True, 
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                out = r.stdout.strip() or r.stderr.strip()
                self.q.put(("status", out[:100]))
                self.q.put(("prog_lbl", "✓"))
            except FileNotFoundError:
                self.q.put(("status", "❌ yt-dlp not found!"))
            except Exception as e:
                self.q.put(("status", f"❌ Update failed: {e}"))
        threading.Thread(target=run, daemon=True).start()

    # ── POLL ─────────────────────────────────
    def _poll(self):
        try:
            while True:
                item = self.q.get_nowait()
                k    = item[0]
                if   k == "row_status":  item[1].set_status(item[2])
                elif k == "row_pct":     item[1].set_pct(item[2])
                elif k == "row_spd":     item[1].set_speed(item[2])
                elif k == "row_size":    item[1].set_size(item[2])
                elif k == "prog_lbl":    self._prog_lbl.configure(text=item[1], fg=GREEN)
                elif k == "status":      self._set_status(item[1])
                elif k == "count":
                    if item[1]:
                        self.ok_count += 1
                        self._s_ok.configure(text=str(self.ok_count))
                    else:
                        self.fail_count += 1
                        self._s_fail.configure(text=str(self.fail_count))
                elif k == "extract_remove_ph":
                    # Stop animation and destroy overlay card
                    _, ph, username = item
                    try:
                        ph._active[0] = False
                        ph.destroy()
                    except Exception:
                        pass
                    if ph in self.rows: self.rows.remove(ph)

                elif k == "extract_row":
                    # Add one video row at a time as they stream in
                    _, title, url, username, count = item
                    sf = username if username else None
                    r  = self._add_row(title, url)
                    r.subfolder  = sf
                    r.is_profile = True
                    if sf:
                        r._save = r._save + "\\" + sf
                        r._save_lbl.configure(text="…\\"+sf)
                    # Update status bar with running count
                    self._set_status(
                        f"🔍 Extracting… {count} found so far — @{username}")
                elif k == "done":
                    self._prog_lbl.configure(text="✓ Done", fg=GREEN)
                    self._set_status(
                        f"Finished  •  ✅ {self.ok_count}  ❌ {self.fail_count}")
        except queue.Empty:
            pass
        self.after(100, self._poll)


if __name__ == "__main__":
    app = VideoGrab()
    app.mainloop()
