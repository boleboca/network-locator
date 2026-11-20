import csv, getpass
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler

rows = list(csv.DictReader(open("devices.csv", encoding="utf-8")))
user = input("Username: ")
pw = getpass.getpass("Password: ")

def collect(d):
    out = {"name": d["hostname"], "ip": d["ip"], "folder": d["folder"],
           "device_name": "", "model": "", "serial": "", "version": "",
           "uptime": "", "status": "ok"}
    try:
        with ConnectHandler(device_type=d["device_type"], host=d["ip"],
                            port=int(d["port"] or 22), username=user,
                            password=pw, conn_timeout=15) as c:
            r = c.send_command("show version", use_textfsm=True)
        if isinstance(r, list) and r:
            r = r[0]
            out["device_name"] = r.get("hostname", "")
            out["model"] = ";".join(r.get("hardware", []))
            out["serial"] = ";".join(r.get("serial", []))
            out["version"] = r.get("version", "")
            out["uptime"] = r.get("uptime", "")
        else:
            out["status"] = "parse failed"
    except Exception as e:
        out["status"] = "FAILED: " + type(e).__name__
    print(out["ip"], out["status"])
    return out

with ThreadPoolExecutor(max_workers=5) as ex:
    results = list(ex.map(collect, rows))

with open("inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader()
    w.writerows(results)

print("Done:", len(results), "devices -> inventory.csv")