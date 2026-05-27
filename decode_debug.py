import base64

def decrypt_url(encoded_str):
    try:
        # Pad encoded_str if needed
        missing_padding = len(encoded_str) % 4
        if missing_padding:
            encoded_str += '=' * (4 - missing_padding)
            
        step1 = base64.b64decode(encoded_str).decode('utf-8', errors='ignore')
        if len(step1) > 16:
            clean_b64 = step1[:12] + step1[16:]
            # Pad clean_b64 if needed
            missing_padding = len(clean_b64) % 4
            if missing_padding:
                clean_b64 += '=' * (4 - missing_padding)
            
            final_url = base64.b64decode(clean_b64).decode('utf-8', errors='ignore')
            return final_url
    except Exception as e:
        return f"Error: {e}"
    return None

encoded = "YUhSMGNITTZMeTkzeFZiZDNjdWFtOXNiSGxuWVcxbExtbDBMM0JwYzJOcGJtVXRhVzUwWlhKeVlYUmxMMnR3Wlc5Mk5UQXlOeTF6ZFcxaGRISmhMWEJwYzJOcGJtVXRhVzUwWlhKeVlYUmxMV2x1TFdGalkybGhhVzh0WkdsdExUVXdNSGd6TURBdFlXeDBaWHA2WVMweE1qQXVhSFJ0YkE9PQ=="
print(f"Decoded: {decrypt_url(encoded)}")
