
import paramiko
import sys

def test_ssh(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connessione a {host} come {user}...")
        client.connect(host, username=user, password=password, timeout=10)
        print("CONNESSO!")
        
        # Eseguiamo qualche comando base
        commands = ["hostname", "uname -a", "ls -l /"]
        for cmd in commands:
            print(f"\nEsecuzione: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            print(stdout.read().decode())
            
        client.close()
    except Exception as e:
        print(f"ERRORE di connessione: {e}")

if __name__ == "__main__":
    # Parametri passati come argomenti o hardcoded per questo test veloce
    host = "195.35.48.73"
    user = "root"
    password = sys.argv[1] if len(sys.argv) > 1 else "Fullparty2026?"
    test_ssh(host, user, password)
