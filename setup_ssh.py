import os
import paramiko
import subprocess

hostname = "192.168.0.134"
username = "ubuntu"
password = "Daikin@2026"

ssh_dir = os.path.expanduser("~/.ssh")
os.makedirs(ssh_dir, exist_ok=True)
key_path = os.path.join(ssh_dir, "id_rsa")
pub_path = key_path + ".pub"

if not os.path.exists(key_path):
    print("Generating SSH key...")
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-N", "", "-f", key_path], check=True)

with open(pub_path, "r") as f:
    pub_key = f.read().strip()

print("Copying key to server...")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(hostname, username=username, password=password)
    client.exec_command(f'mkdir -p ~/.ssh && echo "{pub_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys')
    print("Key copied.")
finally:
    client.close()

# Grab host key for StrictHostKeyChecking
print("Scanning host key...")
res = subprocess.run(["ssh-keyscan", "-H", hostname], capture_output=True, text=True)
if res.returncode == 0:
    known_hosts = os.path.join(ssh_dir, "known_hosts")
    with open(known_hosts, "a") as f:
        f.write(res.stdout)
    print("Host key verified and added.")
