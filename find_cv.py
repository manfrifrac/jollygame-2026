
import paramiko
import sys

def find_cv(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password, timeout=10)
        # Cerchiamo la cartella "cv"
        cmd = "find /root /home -name 'cv' -type d 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd)
        paths = stdout.read().decode().splitlines()
        if paths:
            print("Cartelle 'cv' trovate:")
            for p in paths:
                print(p)
        else:
            print("Nessuna cartella 'cv' trovata in /root o /home.")
        client.close()
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    find_cv("195.35.48.73", "root", "Fullparty2026?")
