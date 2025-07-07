import time

deadline_hex = ''

def seconds_until(deadline):
    deadline_ts = int(deadline, 16)
    now = int(time.time())
    return deadline_ts - now

if __name__ == "__main__":
    print("Seconds until deadline:", seconds_until(deadline_hex))
