import socket
import threading
import time

# ==== CONFIGURATION ====
# CORS NTRIP
NTRIP_HOST = "103.40.12.16"
NTRIP_PORT = 8002
MOUNTPOINT = "RTCM33_GRCEJ"
USERNAME = "ccqq4486"
PASSWORD = "88995"

# M2 module IP on usb0 (Jetson side)
# Usually Jetson assigns itself 192.168.55.1 and M2 is 192.168.55.2 (check with `ifconfig usb0`)
M2_IP = "192.168.55.2"
M2_PORT = 2000  # Replace with M2’s TCP port for UG016/NMEA output

# ==== FUNCTIONS ====
def ntrip_client(sock_to_m2):
    """Connect to NTRIP and forward RTCM corrections to M2 module"""
    import base64
    auth = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    request = (
        f"GET /{MOUNTPOINT} HTTP/1.0\r\n"
        f"Host: {NTRIP_HOST}\r\n"
        f"Ntrip-Version: Ntrip/2.0\r\n"
        f"User-Agent: NTRIP PythonClient/1.0\r\n"
        f"Authorization: Basic {auth}\r\n\r\n"
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((NTRIP_HOST, NTRIP_PORT))
    sock.send(request.encode())
    response = sock.recv(1024)
    if b"200 OK" not in response:
        print("NTRIP connection failed:", response)
        return

    print("NTRIP connected. Streaming RTCM to M2 module...")
    while True:
        data = sock.recv(1024)
        if not data:
            break
        sock_to_m2.sendall(data)

def read_m2_output(sock):
    """Read real-time UG016/NMEA data from M2 module over TCP"""
    def nmea_to_decimal(coord, direction):
        if not coord:
            return None
        deg = int(coord[:2 if direction in "NS" else 3])
        minutes = float(coord[2 if direction in "NS" else 3:])
        dec = deg + minutes / 60
        if direction in "SW":
            dec = -dec
        return dec

    buffer = b""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            buffer += data
            while b'\n' in buffer:
                line, buffer = buffer.split(b'\n', 1)
                line = line.decode(errors="ignore").strip()
                if line.startswith("$GNGGA"):
                    fields = line.split(",")
                    if len(fields) < 15:
                        continue
                    utc_time = fields[1]
                    lat = nmea_to_decimal(fields[2], fields[3])
                    lon = nmea_to_decimal(fields[4], fields[5])
                    fix_quality = fields[6]
                    num_sats = fields[7]
                    alt = fields[9]

                    if utc_time:
                        hh = utc_time[0:2]
                        mm = utc_time[2:4]
                        ss = utc_time[4:6]
                        utc_formatted = f"{hh}:{mm}:{ss}"
                    else:
                        utc_formatted = "N/A"

                    print(f"[{utc_formatted}] Lat: {lat:.6f}, Lon: {lon:.6f}, Alt: {alt}m, Fix: {fix_quality}, Sats: {num_sats}")
        except Exception as e:
            print("M2 read error:", e)
            break

# ==== MAIN ====
if __name__ == "__main__":
    # Connect to M2 over TCP
    sock_m2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_m2.connect((M2_IP, M2_PORT))
    print("Connected to M2 module at", M2_IP)

    # Start NTRIP client in background
    threading.Thread(target=ntrip_client, args=(sock_m2,), daemon=True).start()

    # Read M2 output in main thread
    read_m2_output(sock_m2)
