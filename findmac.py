import csv, re, sys, getpass, keyring
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler

CSV_IN = r"C:\netauto\devices.csv"

if len(sys.argv) < 2:
    sys.exit("usage: python findmac.py aa:bb:cc:dd:ee:ff")
raw = re.sub(r"[^0-9a-f]", "", sys.argv[1].lower())
if len(raw) != 12:
    sys.exit("invalid MAC")
mac = f"{raw[0:4]}.{raw[4:8]}.{raw[8:12]}"

user = keyring.get_password("netauto", "user") or input("Username: ")
pw = keyring.get_password("netauto", "pass") or getpass.getpass("Password: ")

def run(row):
    try:
        with ConnectHandler(device_type=row["device_type"], host=row["ip"],
                            port=int(row["port"] or 22),
                            username=user, password=pw, secret=pw) as c:
            c.enable()
            macs = c.send_command(f"show mac address-table address {mac}", use_textfsm=True)
            if not isinstance(macs, list) or not macs:
                return []
            trunks = c.send_command("show interfaces trunk")
            skip = set(re.findall(r"^(\S+)\s+\S+\s+\S+\s+trunking", trunks, re.M))
        out = []
        for m in macs:
            p = m["destination_port"]
            p = p[0] if isinstance(p, list) else p
            if p not in skip and not p.startswith("Po"):
                out.append((row["hostname"], row["ip"], p, m.get("vlan_id") or m.get("vlan")))
        return out
    except Exception as e:
        return [(row["hostname"], row["ip"], "ERROR", str(e)[:80])]

with open(CSV_IN, newline="") as f:
    devs = list(csv.DictReader(f))

with ThreadPoolExecutor(10) as ex:
    for sub in ex.map(run, devs):
        for r in sub:
            print(r)