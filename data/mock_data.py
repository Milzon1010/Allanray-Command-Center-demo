import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def seed_everything(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)


def now_local():
    return datetime.now()


def make_people(n=35, roles=None):
    roles = roles or ["Driver", "DP", "Gaffer", "Sound", "Grip", "Producer", "Runner", "Warehouse", "Tech"]
    first = ["Adit", "Bima", "Citra", "Dimas", "Eka", "Farah", "Gilang", "Hana", "Intan", "Jaka", "Kiki", "Laras",
             "Mira", "Nanda", "Omar", "Putra", "Raka", "Sari", "Tomi", "Vina", "Wawan", "Yusuf", "Zahra"]
    last = ["Santoso", "Pratama", "Wijaya", "Putri", "Saputra", "Maulana", "Hidayat", "Lestari", "Nugroho", "Ramadhan",
            "Siregar", "Wibowo", "Fauzi", "Kusuma"]

    rows = []
    for i in range(n):
        rows.append((f"AR-{i+1:03d}", f"{random.choice(first)} {random.choice(last)}", random.choice(roles)))
    return pd.DataFrame(rows, columns=["person_id", "name", "role"])


def make_trucks(n_trucks=12, warehouse=None, people=None):
    wh = warehouse or {"lat": -6.200, "lon": 106.816}
    pids = list(people["person_id"]) if people is not None else [f"AR-{i+1:03d}" for i in range(35)]
    rows = []
    for i in range(n_trucks):
        tid = f"TRK-{i+1:02d}"
        plate = f"B {random.randint(1000,9999)} {random.choice(['AR','AY','TS'])}"
        driver_id = random.choice(pids)
        status = random.choice(["MOVING", "IDLE", "ON-SITE"])
        lat = wh["lat"] + np.random.normal(0, 0.03)
        lon = wh["lon"] + np.random.normal(0, 0.03)
        speed = max(0, int(np.random.normal(28, 15))) if status == "MOVING" else max(0, int(np.random.normal(2, 2)))
        fuel_l = max(20, int(np.random.normal(160, 45)))
        rows.append((tid, plate, driver_id, status, float(lat), float(lon), speed, fuel_l))

    return pd.DataFrame(
        rows,
        columns=["truck_id", "plate", "driver_id", "status", "lat", "lon", "speed_kmh", "fuel_liters"]
    )


def make_inventory(equip_categories, projects):
    rows = []
    for cat, n in equip_categories:
        prefix = cat[:2].upper()
        for i in range(n):
            asset_id = f"{prefix}-{i+1:03d}"
            serial = f"{prefix}{random.randint(100000,999999)}"
            status = random.choices(
                ["AVAILABLE", "ON-RENT", "MAINTENANCE", "LOST"],
                weights=[0.62, 0.28, 0.08, 0.02],
                k=1
            )[0]
            project = random.choice(projects) if status == "ON-RENT" else "-"
            assigned = f"AR-{random.randint(1,35):03d}" if status in ["ON-RENT", "MAINTENANCE"] else "-"
            location = random.choice(["WAREHOUSE", "TRUCK", "SITE"]) if status != "LOST" else "UNKNOWN"
            due = (now_local() + timedelta(hours=random.randint(-18, 48))).strftime("%Y-%m-%d %H:%M") if status == "ON-RENT" else "-"
            qr = f"QR:{asset_id}:{serial}"
            rows.append((asset_id, cat, serial, qr, status, project, assigned, location, due))

    return pd.DataFrame(
        rows,
        columns=["asset_id", "category", "serial", "qr_code", "status", "project", "assigned_to", "location", "due_return"]
    )


def make_fuel_tanks():
    tanks = [
        ("TNK-01", "Main Diesel Tank (Warehouse)", 1800),
        ("TNK-02", "Mobile Tank (Support Truck)", 900),
        ("TNK-03", "Genset Tank (On-Site)", 450),
    ]
    rows = []
    for tid, name, cap in tanks:
        level = int(np.clip(np.random.normal(cap * 0.58, cap * 0.18), cap * 0.10, cap * 0.95))
        burn = max(5, int(np.random.normal(32, 10)))
        reorder = int(cap * 0.25)
        rows.append((tid, name, cap, level, burn, reorder))

    return pd.DataFrame(rows, columns=["tank_id", "tank_name", "capacity_l", "level_l", "burn_l_per_day", "reorder_point_l"])


def make_transactions(inv, people, n=140, projects=None):
    projects = projects or ["FILM-A", "FILM-B", "ADS-X", "DOCU-Z"]
    base = now_local() - timedelta(days=3)
    rows = []
    for _ in range(n):
        ts = base + timedelta(minutes=random.randint(0, 3 * 24 * 60))
        a = inv.sample(1).iloc[0]
        p = people.sample(1).iloc[0]
        action = random.choices(["CHECKOUT", "RETURN", "TRANSFER"], weights=[0.45, 0.35, 0.20], k=1)[0]
        project = random.choice(projects)
        note = random.choice(["OK condition", "Needs inspection", "Battery set included", "Packed in hardcase", "Cable count verified"])
        rows.append((ts, action, a["asset_id"], a["category"], p["person_id"], p["name"], project, note))

    df = pd.DataFrame(rows, columns=["time", "action", "asset_id", "category", "person_id", "person_name", "project", "note"])
    return df.sort_values("time", ascending=False).reset_index(drop=True)


def make_alerts(trucks, inv, tanks):
    alerts = []
    now = now_local()

    # Fuel low
    for _, t in tanks.iterrows():
        if t["level_l"] <= t["reorder_point_l"]:
            alerts.append((now, "WARN", f"Fuel low: {t['tank_name']} ({int(t['level_l'])}L) below reorder point."))

    # Overdue returns
    onrent = inv[(inv["status"] == "ON-RENT") & (inv["due_return"] != "-")].copy()

    def parse_due(x):
        try:
            return datetime.strptime(x, "%Y-%m-%d %H:%M")
        except Exception:
            return None

    if len(onrent) > 0:
        onrent["due_dt"] = onrent["due_return"].apply(parse_due)
        od = onrent[(onrent["due_dt"].notna()) & (onrent["due_dt"] < now)]
        if len(od) > 0:
            for _, r in od.sample(min(4, len(od))).iterrows():
                alerts.append((now, "DANGER", f"Overdue return: {r['asset_id']} ({r['category']}) due {r['due_return']} (Project {r['project']})."))

    # Truck moving with low fuel
    lf = trucks[(trucks["status"] == "MOVING") & (trucks["fuel_liters"] < 45)]
    for _, tr in lf.iterrows():
        alerts.append((now, "WARN", f"{tr['truck_id']} moving with low fuel ({tr['fuel_liters']}L). Suggest refuel plan."))

    # Random geofence breach (demo)
    if random.random() < 0.55:
        tr = trucks.sample(1).iloc[0]
        alerts.append((now, "DANGER", f"Geofence alert: {tr['truck_id']} exited Set perimeter (demo). Verify route / authorization."))

    # Lost asset
    lost = inv[inv["status"] == "LOST"]
    if len(lost) > 0:
        r = lost.sample(1).iloc[0]
        alerts.append((now, "DANGER", f"Asset flagged LOST: {r['asset_id']} ({r['category']}). Initiate audit log + last handler lookup."))

    return pd.DataFrame(alerts, columns=["time", "severity", "message"]).sort_values("time", ascending=False)
