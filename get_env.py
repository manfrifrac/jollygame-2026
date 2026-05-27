
import paramiko
import os

def download_env(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        
        # Trova i file .env (possono essercene più di uno, es. .env.example)
        cmd = "find /root/cv -name '.env*' -type f 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd)
        paths = stdout.read().decode().splitlines()
        
        if paths:
            sftp = client.open_sftp()
            for remote_path in paths:
                filename = os.path.basename(remote_path)
                # Salviamo il file nella cartella locale 'cv' che abbiamo appena creato
                local_path = os.path.join(os.getcwd(), "cv", filename)
                
                print(f"File trovato: {remote_path}")
                print(f"Scaricando in: {local_path}")
                sftp.get(remote_path, local_path)
            sftp.close()
            print("\nDOWNLOAD COMPLETATO!")
        else:
            print("Nessun file .env trovato nella cartella /root/cv sulla VPS.")
            
        client.close()
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    download_env("195.35.48.73", "root", "Fullparty2026?")
