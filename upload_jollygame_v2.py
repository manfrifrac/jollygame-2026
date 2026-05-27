
import paramiko
import os
import stat

def mkdir_p(sftp, remote_directory):
    """Crea una directory remota in modo ricorsivo (simile a mkdir -p)"""
    if remote_directory == "/":
        return
    if remote_directory == "" or remote_directory == ".":
        return
    try:
        sftp.chdir(remote_directory) # Se esiste, ci entriamo
    except IOError:
        dirname, basename = os.path.split(remote_directory.rstrip("/"))
        mkdir_p(sftp, dirname)
        sftp.mkdir(basename)
        sftp.chdir(basename)

def upload_dir(sftp, local_dir, remote_dir):
    mkdir_p(sftp, remote_dir)
    print(f"Copia in corso verso: {remote_dir}")
    
    for entry in os.listdir(local_dir):
        # Escludiamo le cartelle pesanti e non compatibili
        if entry in ['venv', 'venv-local', '__pycache__', '.pytest_cache', '.git', '.ssh']:
            continue
            
        local_path = os.path.join(local_dir, entry)
        remote_path = remote_dir + "/" + entry

        if os.path.isdir(local_path):
            upload_dir(sftp, local_path, remote_path)
        else:
            print(f"File: {entry}")
            sftp.put(local_path, remote_path)

def start_upload(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connessione a {host}...")
        client.connect(host, username=user, password=password)
        sftp = client.open_sftp()
        
        local_jolly = os.path.join(os.getcwd(), "JollyGame")
        remote_jolly = "/root/JollyGame"
        
        print(f"Inizio caricamento di JollyGame...")
        upload_dir(sftp, local_jolly, remote_jolly)
        print("\nCARICAMENTO COMPLETATO CON SUCCESSO!")
        
        sftp.close()
        client.close()
    except Exception as e:
        print(f"Errore durante il caricamento: {e}")

if __name__ == "__main__":
    # Caricamento della cartella locale JollyGame verso la VPS
    start_upload("195.35.48.73", "root", "Fullparty2026?")
