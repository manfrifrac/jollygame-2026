import subprocess
import time
import random

def rotate_mullvad():
    try:
        print("🔄 Rotazione VPN Mullvad in corso...")
        # Disconnessione
        subprocess.run(["mullvad", "disconnect"], check=True)
        time.sleep(2)
        
        # Scelta di una località casuale (es. paesi europei per mantenere latenza bassa)
        locations = ["it", "de", "ch", "at", "fr", "es", "nl"]
        loc = random.choice(locations)
        
        print(f"🌍 Connessione a: {loc}...")
        subprocess.run(["mullvad", "relay", "set", "location", loc], check=True)
        subprocess.run(["mullvad", "connect"], check=True)
        
        # Attesa per stabilizzazione
        for i in range(10):
            status = subprocess.run(["mullvad", "status"], capture_output=True, text=True).stdout
            if "Connected" in status:
                print(f"✅ VPN Riconnessa: {status.strip()}")
                return True
            time.sleep(2)
            
        print("❌ Timeout riconnessione VPN.")
        return False
    except Exception as e:
        print(f"❌ Errore durante la rotazione VPN: {e}")
        return False

if __name__ == "__main__":
    rotate_mullvad()
