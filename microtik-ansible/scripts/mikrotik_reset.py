#!usr/bin/env python3
import os
import sys
import time

import pexpect

# Vars send by ansible playbook: /playbooks/00_reset.yml. Vars from file: /group_vars/mikrotik_bootstrap/vars.yml
port = sys.argv[1]
baud = sys.argv[2]
password = os.getenv("BOOTSTRAP_PASS")
new_ip = sys.argv[3]

print(f"Connecting to {port}...")

# pexpect.spawn - pexpect library function. Create process in PTY. Simulate live interactive session.
# f...(string) - add vars from above in {}.
# encoding='utf-8' - convert bytes into string for Python.
# timeout=30 - time for waiting answer from PTY. If no answer - raise pecect.TIMEOUT exeption.
child = pexpect.spawn(f"picocom -b {baud} {port} -q", encoding='utf-8', timeout=30)
# Push picocom session by empty string
child.sendline("")
# Add PTY log to file
child.logfile_read = sys.stdout
# Wating for "login" ask. Add Character class by []. All leters inside will accept.
child.expect(r"[Ll]ogin:\s*", timeout=5)
# Send default "admin"
child.sendline("admin")
# Waiting for "password" ask
child.expect(r"[Pp]assword:\s*", timeout=10)
# Send empty string. (RouterOSv7 default password for admin is empty).
child.sendline("")
# Cycle for skip license: if get MikroTik license asking say "no", else - skip this step.
try:
    license = child.expect(
        [
            r"Do you want to see the software license\? \[Y/n\]:",
            r"Press F1 for help",
            r"\[.*@.*\] > ",
        ],
        timeout=10,
    )
    # If license text will appear - say "no". Else skip step.
    if license == 0:
        print("License promt detected. Bypassing...")
        child.sendline("n\r")
        new_pw = child.expect(
            [
                r"Press F1 for help",
                r"new password:",
                r"\[.*@.*\] > ",
            ],
            timeout=5,
        )
        if new_pw == 0:
            child.sendline("")
        elif new_pw == 1:
            child.sendline("\x03")
    elif license == 1:
        print("Help prompt detected. Bypassing...")
        child.sendline("")
    elif license == 2:
        print("Already in prompt...")
except pexpect.TIMEOUT:
    print("No answer from hardware!")
    sys.exit(1)
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
