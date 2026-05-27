
import base64

def decode_netrivals(encoded):
    try:
        s1 = base64.b64decode(encoded).decode('utf-8', 'ignore')
        # Based on my discovery: noise is at index 12, length 4.
        # But wait, let's look at s1 first.
        return s1
    except: return None

encoded_jolly = "YUhSMGNITTZMeTkzeFZiZDNjdWFtOXNiSGxuWVcxbExtbDBMM0JwYzJOcGJtVXRhVzUwWlhKeVlYUmxMMnR3Wlc5Mk5UQXlOeTF6ZFcxaGRISmhMWEJwYzJOcGJtVXRhVzUwWlhKeVlYUmxMV2x1TFdGalkybGhhVzh0WkdsdExUVXdNSGd6TURBdFlXeDBaWHA2WVMweE1qQXVhSFJ0YkE9PQ=="
encoded_live = "YUhSMGNITTZMeTkzeFZiZDNjdWJHbDJaV2RoY21SbGJpNXBkQzl3YVhOamFXNWhMV2x1ZEdWeWNtRjBZUzFuY21VdGMzVnRZWFJ5WVMxdmRtRnNaUzAxTURBdGVDMHpNREF0ZUMweE1qQXRZMjlrTFd0d1pXOTJOVEF5TnkxbWFXeDBjbTh0YzJGaVltbGhMV1V0WVdOalpYTnpiM0pwTFdOdlpDMDNNVFF5THc9PQ=="

s1_jolly = decode_netrivals(encoded_jolly)
s1_live = decode_netrivals(encoded_live)

print(f"S1 Jolly: {s1_jolly}")
print(f"S1 Live:  {s1_live}")

# Try to find common parts
# aHR0cHM6Ly93 xVbd 3cuam9sbHlnYW1lLml0...
# aHR0cHM6Ly93 xVbd 2cuYmx1M2dhcmRlbi...
