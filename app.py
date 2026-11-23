import subprocess
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import ctypes
import threading
import queue

# =========================================================
# CONFIGURATION
# =========================================================

SCRIPT_DIR = r"C:\netauto"

NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)

BG = "#0f172a"
PANEL = "#1e293b"
INPUT = "#263449"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ACCENT_HOVER = "#0ea5e9"
HOVER = "#334155"

# =========================================================
# PYTHON DETECTION
# =========================================================

def find_py():
    for cmd in (["py", "-3.13"], ["python"]):
        try:
            result = subprocess.run(
                cmd + ["-c", "import netmiko"],
                capture_output=True,
                creationflags=NOWIN
            )
            if result.returncode == 0:
                return cmd
        except FileNotFoundError:
            pass

    return ["python"]


PY = find_py()

# =========================================================
# DARK / COLORED WINDOWS TITLE BAR
# =========================================================

def _colorref(hex_color):
    # "#rrggbb" -> 0x00BBGGRR (Windows COLORREF)
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (b << 16) | (g << 8) | r


def set_dark_titlebar(window):
    try:
        window.update_idletasks()

        # GA_ROOT = 2 -> real top-level window handle
        hwnd = ctypes.windll.user32.GetAncestor(window.winfo_id(), 2)
        dwm = ctypes.windll.dwmapi

        def set_attr(attr, val):
            v = ctypes.c_int(val)
            return dwm.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(v), ctypes.sizeof(v)
            )

        # Dark mode (Win10 20H1+ / Win11), with older fallback
        if set_attr(20, 1) != 0:
            set_attr(19, 1)

        # Windows 11 only: match the app colors
        set_attr(35, _colorref(BG))      # caption color
        set_attr(36, _colorref(TEXT))    # caption text color
        set_attr(34, _colorref(BG))      # window border color
        set_attr(33, 2)                  # rounded corners

        # Force Windows to redraw the frame
        # SWP_NOSIZE | SWP_NOMOVE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x37)

    except Exception:
        pass


# =========================================================
# MODERN DROPDOWN
# =========================================================

class ModernDropdown(tk.Frame):

    ROW_H = 36
    PAD = 6
    TRANSPARENT = "#010203"
    BORDER = "#3b4a63"

    def __init__(self, parent, values, default=None, command=None):
        super().__init__(parent, bg=INPUT)

        self.values = values
        self.value = tk.StringVar(value=default or values[0])
        self.command = command
        self.popup = None

        self.button = tk.Button(
            self,
            text=f"  {self.value.get()}    ▾",
            font=("Segoe UI", 10),
            bg=INPUT,
            fg=TEXT,
            activebackground=HOVER,
            activeforeground=TEXT,
            disabledforeground=MUTED,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=12,
            pady=10,
            command=self.show_menu
        )
        self.button.pack(fill="both", expand=True)

        # Fixed width based on the longest option (button text and popup rows)
        fnt = tkfont.Font(family="Segoe UI", size=10)
        button_w = max(fnt.measure(f"  {v}    ▾") for v in values) + 12 * 2 + 8
        popup_w = max(fnt.measure(v) for v in values) + 40 + 24
        self.fixed_width = max(button_w, popup_w)

        self.update_idletasks()
        self.configure(width=self.fixed_width, height=self.button.winfo_reqheight())
        self.pack_propagate(False)

        self.button.bind("<Enter>", lambda e: self.button.configure(bg=HOVER))
        self.button.bind("<Leave>", lambda e: self.button.configure(bg=INPUT))

        # Close popup when clicking elsewhere or moving/resizing the window
        top = self.winfo_toplevel()
        top.bind("<Button-1>", self._outside_click, add="+")
        top.bind("<Configure>", self._on_configure, add="+")

    # ---------- helpers ----------

    def _round_rect(self, c, x1, y1, x2, y2, r, **kw):
        pts = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1
        ]
        return c.create_polygon(pts, smooth=True, **kw)

    def _outside_click(self, event):
        if event.widget is not self.button:
            self.close_menu()

    def _on_configure(self, event):
        # Only react to the main window itself, not child widgets
        if event.widget is self.winfo_toplevel():
            self.close_menu()

    # ---------- popup ----------

    def show_menu(self):

        if self.popup and self.popup.winfo_exists():
            self.close_menu()
            return

        width = self.fixed_width
        height = len(self.values) * self.ROW_H + self.PAD * 2

        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4

        self.popup = tk.Toplevel(self)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.configure(bg=self.TRANSPARENT)
        self.popup.attributes("-transparentcolor", self.TRANSPARENT)
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        c = tk.Canvas(
            self.popup,
            width=width,
            height=height,
            bg=self.TRANSPARENT,
            highlightthickness=0,
            bd=0
        )
        c.pack()

        # Rounded panel with a subtle border
        self._round_rect(
            c, 1, 1, width - 1, height - 1, 12,
            fill=PANEL, outline=self.BORDER
        )

        current = self.value.get()

        for i, value in enumerate(self.values):
            top = self.PAD + i * self.ROW_H
            bottom = top + self.ROW_H
            selected = value == current
            tag = f"row{i}"

            rect = self._round_rect(
                c, self.PAD + 2, top + 1, width - self.PAD - 2, bottom - 1, 8,
                fill=PANEL, outline="", tags=(tag,)
            )
            c.create_text(
                18, (top + bottom) // 2,
                text="✓" if selected else "",
                fill=ACCENT,
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                tags=(tag,)
            )
            c.create_text(
                40, (top + bottom) // 2,
                text=value,
                fill=ACCENT if selected else TEXT,
                font=("Segoe UI", 10),
                anchor="w",
                tags=(tag,)
            )

            c.tag_bind(
                tag, "<Enter>",
                lambda e, r=rect: (
                    c.configure(cursor="hand2"),
                    c.itemconfigure(r, fill=HOVER)
                )
            )
            c.tag_bind(
                tag, "<Leave>",
                lambda e, r=rect: (
                    c.configure(cursor=""),
                    c.itemconfigure(r, fill=PANEL)
                )
            )
            c.tag_bind(
                tag, "<Button-1>",
                lambda e, v=value: self.select(v)
            )

        self.popup.bind("<Escape>", lambda e: self.close_menu())

    def select(self, value):
        self.value.set(value)
        self.button.configure(text=f"  {value}    ▾")
        self.close_menu()
        if self.command:
            self.command(value)

    def get(self):
        return self.value.get()

    def close_menu(self):
        if self.popup:
            try:
                self.popup.destroy()
            except tk.TclError:
                pass
            self.popup = None


# =========================================================
# SEARCH LOGIC
# =========================================================

result_queue = queue.Queue()

def run():

    q = entry.get().strip()

    if not q:
        entry.focus_set()
        return

    mode = kind.get()

    scripts = {
        "MAC": "findmac.py",
        "IP": "findip.py",
        "Hostname": "findhostname.py"
    }

    script = scripts.get(mode)

    if not script:
        return

    script_path = rf"{SCRIPT_DIR}\{script}"

    # Prevent multiple simultaneous searches
    find_btn.configure(state="disabled")
    kind.button.configure(state="disabled")

    out.configure(state="normal")
    out.delete("1.0", tk.END)
    out.insert(tk.END, f"Searching for {q}...\n\n")
    out.configure(state="disabled")

    def worker():

        try:
            r = subprocess.run(
                PY + [script_path, q],
                capture_output=True,
                text=True,
                creationflags=NOWIN,
                timeout=120
            )

            result_queue.put(("success", r.stdout, r.stderr, r.returncode))

        except subprocess.TimeoutExpired:
            result_queue.put(("error", "Search timed out after 120 seconds.", "", -1))

        except Exception as e:
            result_queue.put(("error", str(e), "", -1))

    threading.Thread(target=worker, daemon=True).start()


def check_results():

    try:
        while True:
            result = result_queue.get_nowait()

            status, stdout, stderr, returncode = result

            out.configure(state="normal")
            out.delete("1.0", tk.END)

            if status == "error":
                out.insert(tk.END, f"ERROR\n\n{stdout}")

            else:
                output_text = stdout or ""

                if stderr:
                    output_text += ("\n" if output_text else "") + stderr

                if not output_text.strip():
                    output_text = "Search completed, but no output was returned."

                out.insert(tk.END, output_text)

                if returncode != 0:
                    out.insert(tk.END, f"\n\nProcess exited with code: {returncode}")

            out.configure(state="disabled")

            find_btn.configure(state="normal")
            kind.button.configure(state="normal")
            entry.focus_set()

    except queue.Empty:
        pass

    root.after(100, check_results)


# =========================================================
# MAIN WINDOW
# =========================================================

root = tk.Tk()

root.title("Network Locator")
root.geometry("800x480")
root.minsize(650, 400)
root.configure(bg=BG)

# Dark title bar
root.after(200, lambda: set_dark_titlebar(root))

# =========================================================
# TTK STYLING
# =========================================================

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "Modern.TButton",
    background=ACCENT,
    foreground=BG,
    font=("Segoe UI", 10, "bold"),
    borderwidth=0,
    padding=(18, 10)
)

style.map(
    "Modern.TButton",
    background=[("active", ACCENT_HOVER), ("disabled", "#334155")],
    foreground=[("disabled", MUTED)]
)

# =========================================================
# HEADER
# =========================================================

header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=28, pady=(25, 15))

tk.Label(
    header,
    text="NETWORK LOCATOR",
    font=("Segoe UI", 9, "bold"),
    fg=ACCENT,
    bg=BG
).pack(anchor="w")

tk.Label(
    header,
    text="Find a device on your network",
    font=("Segoe UI", 22, "bold"),
    fg=TEXT,
    bg=BG
).pack(anchor="w", pady=(5, 3))

tk.Label(
    header,
    text="Search by MAC address, IP address, or hostname.",
    font=("Segoe UI", 10),
    fg=MUTED,
    bg=BG
).pack(anchor="w")

# =========================================================
# SEARCH PANEL
# =========================================================

search_panel = tk.Frame(root, bg=PANEL)
search_panel.pack(fill="x", padx=28, pady=10)

search_row = tk.Frame(search_panel, bg=PANEL)
search_row.pack(fill="x", padx=16, pady=16)

# Custom dropdown
kind = ModernDropdown(
    search_row,
    values=["MAC", "IP", "Hostname"],
    default="MAC"
)
kind.pack(side="left", padx=(0, 10))

# Search input
entry = tk.Entry(
    search_row,
    font=("Segoe UI", 11),
    bg=INPUT,
    fg=TEXT,
    insertbackground=ACCENT,
    relief="flat",
    borderwidth=0
)
entry.pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 10))

entry.bind("<Return>", lambda e: run())

# Find button
find_btn = ttk.Button(
    search_row,
    text="Find  →",
    command=run,
    style="Modern.TButton"
)
find_btn.pack(side="right")

# =========================================================
# RESULTS HEADER
# =========================================================

results_header = tk.Frame(root, bg=BG)
results_header.pack(fill="x", padx=28, pady=(15, 8))

tk.Label(
    results_header,
    text="RESULTS",
    font=("Segoe UI", 9, "bold"),
    fg=MUTED,
    bg=BG
).pack(side="left")

# =========================================================
# RESULTS PANEL
# =========================================================

results_panel = tk.Frame(root, bg=PANEL)
results_panel.pack(fill="both", expand=True, padx=28, pady=(0, 20))

out = tk.Text(
    results_panel,
    font=("Consolas", 10),
    bg=PANEL,
    fg=TEXT,
    insertbackground=ACCENT,
    selectbackground=ACCENT,
    selectforeground=BG,
    relief="flat",
    borderwidth=0,
    padx=15,
    pady=15,
    wrap="word"
)
out.pack(fill="both", expand=True, padx=2, pady=2)

# Initial text
out.insert(
    "1.0",
    "Ready to search...\n\n"
    "Enter a device identifier above and click Find."
)
out.configure(state="disabled")

# =========================================================
# START APPLICATION
# =========================================================

entry.focus_set()

check_results()

root.mainloop()