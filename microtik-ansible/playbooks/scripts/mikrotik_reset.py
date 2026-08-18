#!/usr/bin/env python3
import os
import sys
import pexpect
import time
# Vars send by ansible playbook: /playbooks/00_reset.yml. Vars from file: /group_vars/mikrotik_bootstrap/vars.yml
port = sys.argv[1]
baud = sys.argv[2]
password = os.getenv("BOOTSRAP_PASS")
new_ip = sys.argv[3]

print(f"Connecting to {port}...")

# pexpect.spawn - pexpect library function. Create process in PTY. Simulate live interactive session.
# f...(string) - add vars from above in {}.
# encoding='utf-8' - convert bytes into string for Python.
# timeout=30 - time for waiting answer from PTY. If no answer - raise pecect.TIMEOUT exeption.
child = pexpect.spawn(f"picocom -b {baud} {port} -q", encoding='utf-8', timeout=30)
# Add PTY log to file
child.logfile_read = sys.stdout
# Wating for "login" ask
child.expect(r"login: ")
# Send default "admin"
child.sendline("admin")
# Waiting for "password" ask
child.expect(r"Password: ")
# Send empty string. (RouterOSv7 default password for admin is empty).
child.sendline("")
# Cycle for skip license: if get MikroTik license asking say "no", else - skip this step.
try:
    child.expect(r"Do you want to see the license", timeout=5)
    child.sendline("n")
except pexpect.TIMEOUT:
    pass
# Cycle for skip help: if get MikroTik first help send empty string.
try:
    child.expect(r"Welcome to RouterOS")
    child.sendline("")
except pexpect.TIMEOUT:
    pass
# Skipping new password creating
child.expect(r"new password: ")
child.sendline("\x03")
# Waiting for [admin@MikroTik] string start
child.expect(r"\[.*@.*\] > ")
# Send command reset with no factory defaults
child.sendline("/system reset-configuration no-defaults=yes skip-backup=yes")
# Agree with "Dangerous!"
child.expect(r"y/N")
child.sendline("y")

print("Waiting for device reboot...")
# Pause script to let hardware drop session and full rebooting.
time.sleep(10)
# Waiting 60 sec before login ask. If not - end script.
child.expect(r"login: ", timeout=60)
print("Re-logining after reset...")
child.sendline("admin")
child.expect(r"Password: ")
child.sendline("")
# Setting new password from vars
child.expect(r"new password: ")
child.sendline(f"{password}")
child.expect(r"repeat: ")
child.sendline(f"{password}")
# Set IP address on port Ethernet 1
child.expect(r">")
child.sendline(f"/ip address add address={new_ip} interface=ether1")

print("Bootstrap configuration applied successfully!")
