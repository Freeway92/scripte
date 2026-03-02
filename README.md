# Scripte

Eine Sammlung nützlicher Python-Scripte für Linux.

## Voraussetzungen

```bash
pip install psutil
```

---

## battery_info.py

Zeigt detaillierte Akku-Informationen des Laptops an.

**Ausgabe:**
- Hersteller & Modell
- Ladestand & Status
- Verbleibende Laufzeit
- Energie (aktuell / voll / Design-Kapazität)
- Akkuverschleiß in %
- Spannung & Leistungsaufnahme
- Ladezyklen & Ladelimit

**Verwendung:**
```bash
python3 battery_info.py
```

---

## system_info.py

Zeigt eine vollständige Systemübersicht mit Auslastungsbalken.

**Ausgabe:**
- System (Hostname, OS, Kernel, Uptime)
- CPU (Modell, Takt, Temperatur, Lüfter, Auslastung pro Kern)
- Arbeitsspeicher & Swap/zram
- Speicher (Festplattenauslastung)
- GPU (Intel / NVIDIA / AMD — Takt, Temperatur, Auslastung, VRAM)
- Netzwerk (aktive Interfaces mit IP)
- Akku (Ladestand & Status)

**Verwendung:**
```bash
python3 system_info.py
```

---

## Lizenz

MIT
