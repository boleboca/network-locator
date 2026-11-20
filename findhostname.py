import socket, subprocess, sys

if len(sys.argv) < 2:
    sys.exit("usage: python findname.py HOSTNAME")
try:
    ip = socket.gethostbyname(sys.argv[1])
except socket.gaierror:
    sys.exit("cannot resolve " + sys.argv[1])
print("IP:", ip)
subprocess.run([sys.executable, r"C:\netauto\findip.py", ip])