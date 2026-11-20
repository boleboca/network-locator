import csv, re, sys, getpass, keyring
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler

CSV_IN = r"C:\netauto\devices.csv"

if len(sys.argv) < 2:
    sys.exit("usage: python findip.py 192.0.2.10")
ip = sys.argv[1]

user = keyring.get_password("netauto", "user") or input("Username: ")
pw = keyring.get_password("netauto", "pass") or getpass.getpass("Password: ")

with open(CSV_IN, newline="") as f:
    devs = list(csv.DictReader(f))

def conn(row):
    return ConnectHandler(device_type=row["device_type"], host=row["ip"],
                          port=int(row["port"] or 22),
                          username=user, password=pw, secret=pw)

def arp(row):
    try:
        with conn(row) as c:
            c.enable()
            out = c.send_command(f"show ip arp {ip}")
        m = re.search(r"Internet\s+\S+\s+\S+\s+([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})", out, re.I)
        return m.group(1).lower() if m else None
    except Exception:
        return None

with ThreadPoolExecutor(10) as ex:
    macs = [m for m in ex.map(arp, devs) if m]

if not macs:
    sys.exit("no ARP entry found for " + ip)
mac = macs[0]
print("MAC:", mac)

def find(row):
    try:
        with conn(row) as c:
            c.enable()
            t = c.send_command(f"show mac address-table address {mac}", use_textfsm=True)
            if not isinstance(t, list) or not t:
                return []
            trunks = c.send_command("show interfaces trunk")
            skip = set(re.findall(r"^(\S+)\s+\S+\s+\S+\s+trunking", trunks, re.M))
        out = []
        for m in t:
            p = m["destination_port"]
            p = p[0] if isinstance(p, list) else p
            if p not in skip and not p.startswith("Po"):
                out.append((row["hostname"], row["ip"], p, m.get("vlan_id") or m.get("vlan")))
        return out
    except Exception as e:
        return [(row["hostname"], row["ip"], "ERROR", str(e)[:80])]

with ThreadPoolExecutor(10) as ex:
    for sub in ex.map(find, devs):
        for r in sub:
            print(r)
