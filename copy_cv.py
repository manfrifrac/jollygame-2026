
import paramiko
import os
import stat

def download_dir(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for entry in sftp.listdir_attr(remote_dir):
        remote_path = remote_dir + "/" + entry.filename
        local_path = os.path.join(local_dir, entry.filename)
        if stat.S_ISDIR(entry.st_mode):
            download_dir(sftp, remote_path, local_path)
        else:
            print(f"Scaricando: {remote_path} -> {local_path}")
            sftp.get(remote_path, local_path)

def start_copy(host, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username=user, password=password)
        sftp = client.open_sftp()
        
        remote_cv = "/root/cv"
        local_cv = os.path.join(os.getcwd(), "JollyGame", "cv_vps")
        
        print(f"Inizio copia da {remote_cv} a {local_cv}...")
        download_dir(sftp, remote_cv, local_cv)
        print("\nCOPIA COMPLETATA!")
        
        sftp.close()
        client.close()
    except Exception as e:
        print(f"Errore durante la copia: {e}")

if __name__ == "__main__":
    start_copy("195.35.48.73", "root", "Fullparty2026?")
