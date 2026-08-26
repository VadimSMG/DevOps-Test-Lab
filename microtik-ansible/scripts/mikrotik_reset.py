#!/usr/bin/env python3
import os
import sys
import time

import pexpect

# Vars send by ansible playbook: /playbooks/00_reset.yml. Vars from file: /group_vars/mikrotik_bootstrap/vars.yml
port = sys.argv[1]
baud = sys.argv[2]
password = os.getenv("BOOTSTRAP_PASS")
# Check if password variable exits
if not password:
    print("[-] ERROR: BOOTSTRAP_PASS environment variable is not set!")
    sys.exit(1)
new_ip = sys.argv[3]

# Custom flags for each step
login_u = False # Success login input
login_p = False # Success pasworld input
new_p = False # Success set new password
repeat_p = False # Success repeat new password

print(f"Connecting to {port}...")

# pexpect.spawn - pexpect library function. Create process in PTY. Simulate live interactive session.
# f...(string) - add vars from above in {}.
# encoding='utf-8' - convert bytes into string for Python.
# timeout=30 - time for waiting answer from PTY. If no answer - raise pecect.TIMEOUT exeption.
child = pexpect.spawn(f"picocom -b {baud} {port} -q", encoding='utf-8', timeout=30)
# Add PTY log to file
child.logfile_read = sys.stdout
# Send empty line for pushing picocom
child.sendline("\r")
# Variable for check device boobstrap.
bootstrapped = False
# Variables for check device reset
reset_send = False
# Universal pattern cycle for evry MikroTik serial answer
print("Phase 1: Sending factory reset...")
while True:
    try:
        idx = child.expect(
            [
                r"[Mm]ikro[Tt]ik [Ll]ogin:\s*", # 0 CLI login (RouterOSv7: "MikroTik Login")
                r"[Pp]assword:\s*", # 1 CLI access password (RouterOSv7: "")
                r"Do you want to see the software license\? \[Y/n\]:", # 2 EULA prorposal afret reset
                r"Press F1 for help", # 3 Default condfig message after reset
                r"[Nn]ew password>\s*", # 4 Asking for new password after reset
                r"[Rr]epeat new password>\s*", # 5 Asking for repeat new password after reset
                r"\[.*@.*\] > ", # 6 Get console header [admin@MikroTik]
                r"[Dd]angerous\!*.", # 7 Warning before full reset
                r"\x1b\[[0-9;]*[a-zA-Z]", # 8 Ignoring DSR (Device Status Report) messages
                r"--More--", # 9 Skipping for paging output
                pexpect.TIMEOUT, # 10 Timeout patern
            ],
            timeout=10,
        )
        if idx == 0:
            if not login_u:
                print("Loggining in CLI...")
                child.sendline("admin") # Default login RouterOSv7: "admin"
                login_u = True
            else:
                continue
        elif idx == 1:
            if not login_p:
                print("Sending password...")
                child.sendline(password if bootstrapped else "\r") # Default password RouterOSv7 is empty
                login_p = True
            else:
                continue
        elif idx == 2:
            print("Skipping EULA...")
            child.sendline("n\r") # Send "No" for license prompt
        elif idx == 3:
            if reset_send:
                print("Skipping Welcome message...")
                child.sendline("\r") # Send empty string for skip welcome message
            else:
                continue
        elif idx == 4:
            if not bootstrapped:
                if not reset_send:
                    print("Bypassing new password...")
                    child.sendcontrol("c")
                    time.sleep(1)
                else:
                    print("Reset already triggered...")
                    continue
            else:
                if not new_p:
                    print("Setting new password...")
                    child.sendline(password+"\r") 
                    new_p = True
                else:
                    continue
        elif idx == 5:
            if not repeat_p:
                print("Repeating new password...")
                child.sendline(password)
                repeat_p = True
            else:
                continue
        elif idx == 6:
            if not reset_send:
                print("Reached CLI. Triggering factory reset...") 
                child.sendline("/system reset-configuration no-defaults=yes skip-backup=yes\r") # Send bootstrap command 
                reset_send = True
            elif bootstrapped:
                print("Successfully logged in! Setting static IP...")
                child.sendline(f"/ip address add address={new_ip}/24 interface=ether1")
                time.sleep(2)
                break
        elif idx == 7:
            print("Confirming factory reset!")
            child.sendline("y\r")
            bootstrapped = True
            login_u = False
            login_p = False
            print("Factory reset initiated! Waitng for reboot 60 sec")
            time.sleep(60)
        elif idx == 8:
            child.sendline("\r")
            continue
        elif idx == 9:
            child.sendline(" ") # Send space for sipping pagening "--More--"
        elif idx == 10:
            raise TimeoutError ("Hardware stuck or stop answering!") 
    except pexpect.TIMEOUT:
        print("[-] Hardware unresponsive.")
        sys.exit(1)
print("Bootstraping complete! EOF")
child.sendcontrol("a")
child.sendcontrol("x")
child.close()
sys.exit(0)
