import csv, getpass, os, re, datetime
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler

rows = list(csv.DictReader(open("devices.csv", encoding="utf-8")))
import keyring
user = keyring.get_password("netauto", "user") or input("Username: ")
pw = keyring.get_password("netauto", "pass") or getpass.getpass("Password: ")

folder = os.path.join("backups", datetime.date.today().isoformat())
os.makedirs(folder, exist_ok=True)

def backup(d):
    name = re.sub(r'[\\/:*?"<>|\s]+', "_", d["hostname"]) + "_" + d["ip"]
    try:
        with ConnectHandler(device_type=d["device_type"], host=d["ip"],
                            port=int(d["port"] or 22), username=user,
                            password=pw, conn_timeout=15) as c:
            cfg = c.send_command("show running-config", read_timeout=90)
        with open(os.path.join(folder, name + ".cfg"), "w", encoding="utf-8") as f:
            f.write(cfg)
        res = "ok"
    except Exception as e:
        res = "FAILED: " + type(e).__name__
    print(d["ip"], res)
    return [d["hostname"], d["ip"], res]

with ThreadPoolExecutor(max_workers=5) as ex:
    out = list(ex.map(backup, rows))

with open(os.path.join(folder, "_summary.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["hostname", "ip", "result"])
    w.writerows(out)

print("Done:", sum(1 for o in out if o[2] == "ok"), "of", len(out), "backed up ->", folder)