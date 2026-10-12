import paramiko
import sys

if len(sys.argv) < 2:
    print("Usage: python ssh_exec.py <command>")
    sys.exit(1)

command = " ".join(sys.argv[1:])
hostname = "192.168.0.134"
username = "ubuntu"
password = "Daikin@2026"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect(hostname, username=username, password=password)
    stdin, stdout, stderr = client.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out, end='')
    if err:
        print(err, end='', file=sys.stderr)
    sys.exit(exit_status)
except Exception as e:
    print(f"SSH Error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    client.close()
