# Network Locator

Find which switch port a device is on, by MAC, IP or hostname. Netmiko scripts for Cisco IOS switches, plus a small tkinter GUI and a config backup script.

## Setup

1. Install Python 3.13 and run `pip install -r requirements.txt`
2. Copy the scripts to `C:\netauto` and create `devices.csv` from `devices.example.csv`
3. Store switch credentials once: `python -c "import keyring,getpass;keyring.set_password('netauto','user',input('User: '));keyring.set_password('netauto','pass',getpass.getpass('Pass: '))"`

## Usage

`python findmac.py aa:bb:cc:dd:ee:ff`
`python findip.py 192.0.2.10`
`python findhostname.py HOSTNAME`
`python app.py` opens the GUI
`python backup.py` backs up all switch configs
