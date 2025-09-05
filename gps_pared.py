import serial
import time

def parse_gga(sentence):
    parts = sentence.split(',')
    if len(parts) < 15:
        return None
    try:
        lat_raw = parts[2]
        lat = float(lat_raw[:2]) + float(lat_raw[2:]) / 60.0 if lat_raw else None
        if parts[3] == "S": lat = -lat

        lon_raw = parts[4]
        lon = float(lon_raw[:3]) + float(lon_raw[3:]) / 60.0 if lon_raw else None
        if parts[5] == "W": lon = -lon

        fix_quality = int(parts[6]) if parts[6] else 0
        fix_types = {0:"Invalid",1:"GPS Fix",2:"DGPS Fix",4:"RTK Fixed",5:"RTK Float"}

        return {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "source": "GGA",
            "lat": lat,
            "lon": lon,
            "alt": float(parts[9]) if parts[9] else None,
            "fix_type": fix_types.get(fix_quality, f"Unknown({fix_quality})"),
            "sats": int(parts[7]) if parts[7] else 0,
            "hdop": float(parts[8]) if parts[8] else None,
        }
    except:
        return None


def parse_bestposa(sentence):
    parts = sentence.split(',')
    if len(parts) < 20:
        return None
    try:
        return {
            "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "source": "BESTPOSA",
            "lat": float(parts[12]),
            "lon": float(parts[13]),
            "alt": float(parts[14]),
            "fix_type": f"{parts[10].strip()}-{parts[11].strip()}",
            "datum": parts[16],
            "accuracy": (float(parts[18]), float(parts[19]), float(parts[20])),
        }
    except:
        return None


def main():
    #port = "/dev/ttyUSB0"
    port = "/dev/m2_rtk"
    baudrate = 115200

    last_print_time = 0

    with serial.Serial(port, baudrate, timeout=1) as ser:
        print(f"Listening on {port} ...")
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue

            result = None
            if line.startswith("$GPGGA"):
                result = parse_gga(line)
            elif line.startswith("#BESTPOSA"):
                result = parse_bestposa(line)

            if result:
                now = time.time()
                print(result)
                last_print_time = now


if __name__ == "__main__":
    main()

