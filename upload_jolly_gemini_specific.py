
import paramiko
import os

def upload_jolly_gemini(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        sftp = client.open_sftp()
        
        # Percorsi specifici per il file gemini dentro JollyGame
        local_path = os.path.join(os.getcwd(), "JollyGame", "GEMINI.md")
        remote_path = "/root/JollyGame/GEMINI.md"
        
        if os.path.exists(local_path):
            print(f"Caricamento {local_path} -> {remote_path}...")
            sftp.put(local_path, remote_path)
            print("CARICAMENTO COMPLETATO!")
        else:
            print(f"Errore: il file locale {local_path} non esiste.")
            
        sftp.close()
        client.close()
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    upload_jolly_gemini("195.35.48.73", "root", "Fullparty2026?")
