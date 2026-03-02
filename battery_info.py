import psutil
import sys


def read_sys(filename):
    try:
        with open(f"/sys/class/power_supply/BAT0/{filename}") as f:
            return f.read().strip()
    except OSError:
        return None


def format_time(seconds):
    if seconds == psutil.POWER_TIME_UNKNOWN:
        return "Unbekannt"
    if seconds == psutil.POWER_TIME_UNLIMITED:
        return "Stromversorgung aktiv"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m:02d}m"


def get_battery_info():
    battery = psutil.sensors_battery()

    if battery is None:
        print("Kein Akku gefunden.")
        sys.exit(1)

    status = "Wird geladen" if battery.power_plugged else "Entladen"
    time_str = format_time(battery.secsleft)

    # Werte aus /sys/class/power_supply/BAT0/
    energy_now    = read_sys("energy_now")
    energy_full   = read_sys("energy_full")
    energy_design = read_sys("energy_full_design")
    power_now     = read_sys("power_now")
    voltage_now   = read_sys("voltage_now")
    voltage_min   = read_sys("voltage_min_design")
    cycle_count   = read_sys("cycle_count")
    technology    = read_sys("technology")
    manufacturer  = read_sys("manufacturer")
    model_name    = read_sys("model_name")
    capacity_lvl  = read_sys("capacity_level")
    charge_start  = read_sys("charge_control_start_threshold")
    charge_end    = read_sys("charge_control_end_threshold")

    # Umrechnung: µWh -> Wh, µW -> W, µV -> V
    def uwh(val):
        return f"{int(val) / 1_000_000:.2f} Wh" if val else "–"

    def uw(val):
        return f"{int(val) / 1_000_000:.2f} W" if val else "–"

    def uv(val):
        return f"{int(val) / 1_000_000:.3f} V" if val else "–"

    # Akkuverschleiß in %
    wear = None
    if energy_full and energy_design and int(energy_design) > 0:
        wear = (1 - int(energy_full) / int(energy_design)) * 100

    print("=" * 42)
    print("          Akku-Informationen")
    print("=" * 42)
    print(f"  Hersteller:       {manufacturer or '–'} {model_name or ''}")
    print(f"  Technologie:      {technology or '–'}")
    print()
    print(f"  Ladestand:        {battery.percent:.1f}%  ({capacity_lvl or '–'})")
    print(f"  Status:           {status}")
    print(f"  Verbleibend:      {time_str}")
    print()
    print(f"  Energie (jetzt):  {uwh(energy_now)}")
    print(f"  Energie (voll):   {uwh(energy_full)}")
    print(f"  Energie (Design): {uwh(energy_design)}")
    if wear is not None:
        print(f"  Akkuverschleiß:   {wear:.1f}%")
    print()
    print(f"  Leistung:         {uw(power_now)}")
    print(f"  Spannung:         {uv(voltage_now)}")
    print(f"  Min. Spannung:    {uv(voltage_min)}")
    print()
    print(f"  Ladezyklen:       {cycle_count or '–'}")
    if charge_start and charge_end:
        print(f"  Ladelimit:        {charge_start}% – {charge_end}%")
    print("=" * 42)


if __name__ == "__main__":
    get_battery_info()
