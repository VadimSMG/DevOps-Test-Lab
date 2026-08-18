#!/usr/bin/env python3
import sys
import pexpect

port = sys.argv[1]
password = sys.argv[2]
new_ip = sys.argv[3]

print(f"Connecting to {port}...")
# Запускаємо picocom абопрямо відкриваємо порт через pexpect
child = pexpect.spawn(f"picocom -b 115200 {port} -q", encoding='utf-8', timeout=30)

# Логіка очікування та відповіді
child.expect([r"login:", r"Password:"])
child.sendline("admin")

# Якщо це новий або скинутий девайс, приймаємо ліцензію
try:
    child.expect(r"Do you want to see the license", timeout=5)
    child.sendline("n")
except pexpect.TIMEOUT:
    pass

# Встановлюємо новий пароль та IP
child.expect(r">")
child.sendline(f"/user set admin password={password}")

child.expect(r">")
child.sendline(f"/ip address add address={new_ip} interface=ether1")

print("Bootstrap configuration applied successfully!")

