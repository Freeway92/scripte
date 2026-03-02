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
    uname = platform.uname()
    uptime_s = int(psutil.boot_time())
    import time
    uptime = int(time.time()) - uptime_s
    h, m = divmod(uptime // 60, 60)
    hostname = os.uname().nodename
    print(f"  Hostname:     {hostname}")
    print(f"  OS:           {platform.system()} {platform.release()}")
    print(f"  Kernel:       {uname.version.split()[0] if uname.version else uname.release}")
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
