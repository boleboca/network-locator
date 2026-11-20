import csv, re, sys

src = sys.argv[1]
seen = {}
folder = ""

with open(src, encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if line.startswith("SubRep="):
            folder = line.split("=", 1)[1]
            continue
        m = re.match(r"^(.+?)=#109#0%([^%]+)%(\d*)%", line)
        if not m:
            continue
        name, host, port = m.groups()
        if host in seen:
            continue
        seen[host] = [name.strip(), host, port or "22", folder, ""]

with open("devices.csv", "w", newline="", encoding="utf-8") as out:
    w = csv.writer(out)
    w.writerow(["hostname", "ip", "port", "folder", "device_type"])
    w.writerows(seen.values())

print(len(seen), "devices written to devices.csv")