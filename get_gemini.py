
import paramiko
import os

def download_gemini(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        
        # Trova il file GEMINI.md
        cmd = "find /root -name 'GEMINI.md' -type f 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd)
        paths = stdout.read().decode().splitlines()
        
        if paths:
            remote_path = paths[0]
            local_path = os.path.join(os.getcwd(), "GEMINI.md")
            print(f"File trovato in: {remote_path}")
            
            sftp = client.open_sftp()
            print(f"Scaricando {remote_path} -> {local_path}")
            sftp.get(remote_path, local_path)
            sftp.close()
            print("DOWNLOAD COMPLETATO!")
        else:
            print("File GEMINI.md non trovato sulla VPS.")
            
        client.close()
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    download_gemini("195.35.48.73", "root", "Fullparty2026?")
