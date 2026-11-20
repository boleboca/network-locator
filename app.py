import subprocess, tkinter as tk
from tkinter import ttk

NOWIN = subprocess.CREATE_NO_WINDOW

def find_py():
    for cmd in (["py", "-3.13"], ["python"]):
        try:
            if subprocess.run(cmd + ["-c", "import netmiko"],
                              capture_output=True, creationflags=NOWIN).returncode == 0:
                return cmd
        except FileNotFoundError:
            pass
    return ["python"]

PY = find_py()

def run():
    q = entry.get().strip()
    if not q:
        return
    mode = kind.get()
    script = {"MAC": "findmac.py", "IP": "findip.py", "Hostname": "findhostname.py"}[mode]
    out.delete("1.0", tk.END)
    out.insert(tk.END, "Searching...\n")
    root.update()
    r = subprocess.run(PY + [rf"C:\netauto\{script}", q],
                       capture_output=True, text=True, creationflags=NOWIN)
    out.delete("1.0", tk.END)
    out.insert(tk.END, r.stdout + r.stderr)

root = tk.Tk()
root.title("Network Locator")
root.geometry("720x380")
top = ttk.Frame(root); top.pack(fill="x", padx=10, pady=10)
kind = ttk.Combobox(top, values=["MAC", "IP", "Hostname"], state="readonly", width=10)
kind.current(0); kind.pack(side="left")
entry = ttk.Entry(top); entry.pack(side="left", fill="x", expand=True, padx=8)
entry.bind("<Return>", lambda e: run())
ttk.Button(top, text="Find", command=run).pack(side="left")
out = tk.Text(root, font=("Consolas", 10)); out.pack(fill="both", expand=True, padx=10, pady=(0, 10))
root.mainloop()