import os
import platform
import subprocess
import psutil


def bar(percent, width=20):
    filled = int(width * percent / 100)
    return f"[{'█' * filled}{'░' * (width - filled)}] {percent:.1f}%"


def read_sys(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return None


def get_temps():
    try:
        out = subprocess.check_output(["sensors"], text=True)
    except FileNotFoundError:
        return None, None

    cpu_temp = None
    fan_rpm = None

    for line in out.splitlines():
        if line.startswith("CPU:") and cpu_temp is None:
            try:
                cpu_temp = float(line.split("+")[1].split("°")[0])
            except (IndexError, ValueError):
                pass
        if line.startswith("fan1:") and fan_rpm is None:
            try:
                fan_rpm = int(line.split()[1])
            except (IndexError, ValueError):
                pass

    return cpu_temp, fan_rpm


def get_gpu_info():
    gpus = []

    # NVIDIA
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,clocks.current.graphics",
             "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        )
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            gpus.append({
                "typ": "NVIDIA",
                "name": parts[0],
                "temp": f"{parts[1]}°C" if parts[1] != "[N/A]" else None,
                "auslastung": float(parts[2]) if parts[2] not in ("[N/A]", "") else None,
                "vram_used": int(parts[3]) if parts[3] not in ("[N/A]", "") else None,
                "vram_total": int(parts[4]) if parts[4] not in ("[N/A]", "") else None,
                "takt": f"{parts[5]} MHz" if parts[5] not in ("[N/A]", "") else None,
            })
        if gpus:
            return gpus
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # AMD
    try:
        out = subprocess.check_output(["lspci"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if "AMD" in line and ("VGA" in line or "Display" in line or "3D" in line):
                name = line.split(":")[-1].strip()
                temp = read_sys("/sys/class/drm/card0/device/hwmon/hwmon0/temp1_input")
                takt_cur = read_sys("/sys/class/drm/card0/device/pp_dpm_sclk")
                gpus.append({
                    "typ": "AMD",
                    "name": name,
                    "temp": f"{int(temp) / 1000:.1f}°C" if temp else None,
                    "takt": takt_cur,
                    "auslastung": None,
                    "vram_used": None,
                    "vram_total": None,
                })
        if gpus:
            return gpus
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Intel
    try:
        out = subprocess.check_output(["lspci"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if "Intel" in line and ("VGA" in line or "Display" in line):
                name = line.split(":")[-1].strip()
                takt_cur = read_sys("/sys/class/drm/card0/gt_cur_freq_mhz")
                takt_max = read_sys("/sys/class/drm/card0/gt_boost_freq_mhz")
                # GPU-Temperatur aus thinkpad-Sensor (falls vorhanden)
                gpu_temp = None
                for hwmon in os.listdir("/sys/class/hwmon"):
                    base = f"/sys/class/hwmon/{hwmon}"
                    name_val = read_sys(f"{base}/name")
                    if name_val == "thinkpad":
                        raw = read_sys(f"{base}/temp2_input")
                        if raw and int(raw) > 0:
                            gpu_temp = f"{int(raw) / 1000:.1f}°C"
                        break
                gpus.append({
                    "typ": "Intel",
                    "name": name,
                    "temp": gpu_temp,
                    "takt": f"{takt_cur} MHz (max {takt_max} MHz)" if takt_cur and takt_max else None,
                    "auslastung": None,
                    "vram_used": None,
                    "vram_total": None,
                })
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    return gpus


def get_battery():
    base = "/sys/class/power_supply/BAT0"
    capacity = read_sys(f"{base}/capacity")
    status = read_sys(f"{base}/status")
    if capacity is None:
        return None
    status_map = {"Charging": "Wird geladen", "Discharging": "Entladen", "Full": "Voll"}
    return int(capacity), status_map.get(status, status)


def section(title):
    print(f"\n  {'─' * 38}")
    print(f"  {title}")
    print(f"  {'─' * 38}")


def main():
    print("=" * 42)
    print("        System-Informationen")
    print("=" * 42)

    # System
    section("System")
    uptime_s = int(psutil.boot_time())
    import time
    uptime = int(time.time()) - uptime_s
    h, m = divmod(uptime // 60, 60)
    hostname = os.uname().nodename

    os_name = None
    os_release_path = "/etc/os-release"
    if os.path.exists(os_release_path):
        with open(os_release_path) as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    os_name = line.split("=", 1)[1].strip().strip('"')
                    break
    if not os_name:
        os_name = f"{platform.system()} {platform.release()}"

    print(f"  Hostname:     {hostname}")
    print(f"  OS:           {os_name}")
    print(f"  Kernel:       {platform.release()}")
    print(f"  Uptime:       {h}h {m:02d}m")

    # CPU
    section("CPU")
    cpu_freq = psutil.cpu_freq()
    cpu_usage = psutil.cpu_percent(interval=0.5, percpu=True)
    cpu_temp, fan_rpm = get_temps()

    print(f"  Modell:       {platform.processor() or 'Intel Core i7-8550U'}")
    if cpu_freq:
        print(f"  Takt:         {cpu_freq.current:.0f} MHz  (max {cpu_freq.max:.0f} MHz)")
    if cpu_temp:
        print(f"  Temperatur:   {cpu_temp:.1f}°C")
    if fan_rpm is not None:
        print(f"  Lüfter:       {fan_rpm} RPM" if fan_rpm > 0 else "  Lüfter:       Aus")
    print(f"  Gesamt:       {bar(sum(cpu_usage) / len(cpu_usage))}")
    for i, u in enumerate(cpu_usage):
        print(f"  Kern {i}:        {bar(u)}")

    # RAM
    section("Arbeitsspeicher")
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    print(f"  RAM:          {bar(ram.percent)}  ({ram.used / 1e9:.1f} / {ram.total / 1e9:.1f} GB)")
    print(f"  Swap/zram:    {bar(swap.percent)}  ({swap.used / 1e9:.1f} / {swap.total / 1e9:.1f} GB)")

    # Festplatte
    section("Speicher")
    for part in psutil.disk_partitions():
        if part.mountpoint not in ("/", "/home") and not part.mountpoint.startswith("/boot"):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            print(f"  {part.mountpoint:<14}{bar(usage.percent)}  ({usage.used / 1e9:.1f} / {usage.total / 1e9:.1f} GB)")
        except PermissionError:
            pass

    # GPU
    gpus = get_gpu_info()
    if gpus:
        section("GPU")
        for gpu in gpus:
            print(f"  Typ:          {gpu['typ']}")
            print(f"  Modell:       {gpu['name']}")
            if gpu["temp"]:
                print(f"  Temperatur:   {gpu['temp']}")
            if gpu["takt"]:
                print(f"  Takt:         {gpu['takt']}")
            if gpu["auslastung"] is not None:
                print(f"  Auslastung:   {bar(gpu['auslastung'])}")
            if gpu["vram_used"] is not None and gpu["vram_total"] is not None:
                vram_pct = gpu["vram_used"] / gpu["vram_total"] * 100
                print(f"  VRAM:         {bar(vram_pct)}  ({gpu['vram_used']} / {gpu['vram_total']} MB)")

    # Netzwerk
    section("Netzwerk")
    net = psutil.net_if_addrs()
    net_stats = psutil.net_if_stats()
    for iface, addrs in net.items():
        if iface == "lo":
            continue
        for addr in addrs:
            if addr.family == 2:  # IPv4
                is_up = net_stats[iface].isup if iface in net_stats else False
                status = "✓" if is_up else "✗"
                print(f"  {status} {iface:<12} {addr.address}")

    # Akku
    battery = get_battery()
    if battery:
        section("Akku")
        cap, status = battery
        print(f"  Status:       {status}")
        print(f"  Ladestand:    {bar(cap)}")

    print("\n" + "=" * 42)


if __name__ == "__main__":
    main()
