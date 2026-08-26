#!/usr/bin/env python3
import argparse
import sys
import time

import pexpect

# Using argsparse object. Vars sendeing throu /playbooks.00_reset.yml from file /group_vars/mikrotik_bootstrap/vars.yml
parser = argparse.ArgumentParser(description="MikroTik Serial Bootstrap FSM")
parser.add_argument("port", help="Serial port (e.g., /dev/ttyS0)")
parser.add_argument("ip", help="Temporary static IP to assign (e.g., 192.168.13.2)")
parser.add_argument("baud", help="Baudrate connection speed (e.g., 115200)")
args = parser.parse_args()

# Vars send by ansible playbook: /playbooks/00_reset.yml. Vars from file: /group_vars/mikrotik_bootstrap/vars.yml
#password = os.getenv("BOOTSTRAP_PASS")
# Check if password variable exits
#if not password:
    #print("[-] ERROR: BOOTSTRAP_PASS environment variable is not set!")
    #sys.exit(1)

# Custom flags for each step
login_u = False # Success login input
login_p = False # Success pasworld input
bypass_p = False # Success EULA skip
#new_p = False # Success set new password
#repeat_p = False # Success repeat new password

print(f"Connecting to {args.port}...")

# pexpect.spawn - pexpect library function. Create process in PTY. Simulate live interactive session.
# f...(string) - add vars from above in {}.
# encoding='utf-8' - convert bytes into string for Python.
# timeout=30 - time for waiting answer from PTY. If no answer - raise pecect.TIMEOUT exeption.
child = pexpect.spawn(f"picocom -b {args.baud} {args.port} -q", encoding='utf-8', timeout=30)
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
                r"Try again, error: New password is the same as old one", # 6 Error from repeating old password
                r"\[.*@.*\] > ", # 7 Get console header [admin@MikroTik]
                r"[Dd]angerous\!*.", # 8 Warning before full reset
                r"\x1b\[[0-9;]*[a-zA-Z]", # 9 Ignoring DSR (Device Status Report) messages
                r"--More--", # 10 Skipping for paging output
                pexpect.TIMEOUT, # 11 Timeout patern
            ],
            timeout=20,
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
                child.sendline("\r") # Default password RouterOSv7 is empty
                login_p = True
                time.sleep(2)
            else:
                continue
        elif idx == 2:
            print("Skipping EULA...")
            child.sendline("n") # Send "No" for license prompt
        elif idx == 3:
            print("Skipping Welcome message...")
            child.sendline("\r") # Send empty string for skip welcome message
        elif idx == 4 or idx == 5:
            if not bypass_p:
                print("Bypassing new password...")
                child.sendcontrol("c")
                bypass_p = True
                time.sleep(1)
            else:
                continue
        elif idx == 6:
            print("WARNING: This password in already in use. Set the different password!")
            continue
        elif idx == 7:
            if not reset_send:
                print("Reached CLI. Triggering factory reset...") 
                child.sendline("/system reset-configuration no-defaults=yes skip-backup=yes") # Send bootstrap command 
                reset_send = True
            elif bootstrapped:
                print("Successfully logged in! Setting static IP...")
                child.sendline(f"/ip address add address={args.ip}/24 interface=ether1")
                time.sleep(2)
                break
        elif idx == 8:
            print("Confirming factory reset!")
            child.sendline("y")
            bootstrapped = True
            login_u = False
            login_p = False
            bypass_p = False
            print("Factory reset initiated! Waitng for reboot 60 sec")
            time.sleep(60)
        elif idx == 9:
            #child.sendline("\r")
            continue
        elif idx == 10:
            child.sendline(" ") # Send space for sipping pagening "--More--"
        elif idx == 11:
            raise TimeoutError ("Hardware stuck or stop answering!") 
    except pexpect.TIMEOUT:
        print("[-] Hardware unresponsive.")
        sys.exit(1)
print("Bootstraping complete! EOF")
child.sendcontrol("a")
child.sendcontrol("x")
child.close()
sys.exit(0)
