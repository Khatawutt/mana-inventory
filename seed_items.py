import os, sqlite3, openpyxl

EXCEL_PATH = r"C:\Users\Khatawutt's PC\AppData\Local\hermes\attachments\ระบบ Inventory MANA Garden (Master System) - Linked.xlsx"
DB_PATH = r"C:\Users\Khatawutt's PC\MANA GARDEN Inventory\mana_inventory.db"

def parse_excel(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    items = []
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        header_idx = None
        for i, row in enumerate(rows):
            if row and any(c and str(c).strip().upper() == 'CODE' for c in row):
                header_idx = i
                break
        if header_idx is None:
            continue
        header = [str(c).strip().upper() if c else "" for c in rows[header_idx]]
        if ws.title and ("daily" in ws.title.lower() or "count log" in ws.title.lower()):
            continue
        col = {}
        for i, h in enumerate(header):
            if h:
                col[h] = i
        cat = "kitchen" if "kitchen" in ws.title.lower() else ("cafe" if "cafe" in ws.title.lower() else "general")
        for row in rows[header_idx+1:]:
            if row is None or all(c is None or str(c).strip() == "" for c in row):
                continue
            code = row[col.get('CODE', -1)]
            if code is None or str(code).strip() == "":
                continue
            code = str(code).strip()
            name = row[col.get('ชื่อสินค้าคงคลัง', col.get('ชื่อสินค้า', -1))]
            if name is None or str(name).strip() == "":
                name = code
            else:
                name = str(name).strip()
            unit = row[col.get('หน่วยนับ', col.get('หน่วย', -1))] or 'ea'
            opening = row[col.get('ยอดยกมา (OPENING)'.upper(), col.get('ยอดยกมา (Opening)', -1))] or 0
            received = row[col.get('ยอดรับเข้า (RECEIVED)'.upper(), col.get('ยอดรับเข้า (Received)', -1))] or 0
            used = row[col.get('ยอดจ่ายออก (USED)'.upper(), col.get('ยอดจ่ายออก (Used)', -1))] or 0
            ending = row[col.get('คงเหลือปลายงวด (ENDING)'.upper(), col.get('คงเหลือปลายงวด (Ending)', -1))] or 0
            par = row[col.get('จุดสั่งซื้อซ้ำ (PAR LEVEL)'.upper(), col.get('จุดสั่งซื้อซ้ำ (PAR Level)', -1))] or 0
            status = None
            for k in col:
                if 'สถานะ' in k:
                    status = row[col[k]]
                    break
            if status is None or str(status).strip() == "":
                status = "ปกติ" if (ending or 0) >= (par or 0) else "ต้องสั่งซื้อ"
            else:
                status = str(status).strip()
            items.append((code, name, str(unit).strip(), cat,
                         int(opening or 0), int(received or 0), int(used or 0),
                         int(ending or 0), int(par or 0), status))
    return items

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    db = sqlite3.connect(DB_PATH)
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','kitchen','cafe')),
        phone TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, unit TEXT NOT NULL,
        category TEXT NOT NULL DEFAULT 'general', opening INTEGER DEFAULT 0, received INTEGER DEFAULT 0,
        used INTEGER DEFAULT 0, ending INTEGER DEFAULT 0, par INTEGER DEFAULT 0, status TEXT NOT NULL DEFAULT 'ปกติ',
        location TEXT DEFAULT 'Main Store', created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS counts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL, location TEXT NOT NULL DEFAULT 'Main Store',
        counted_by TEXT NOT NULL, count_date TEXT NOT NULL, physical_qty INTEGER NOT NULL,
        note TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    );
    CREATE INDEX idx_counts_item ON counts(item_id, count_date);
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER NOT NULL, qty INTEGER NOT NULL,
        unit_cost REAL DEFAULT 0, note TEXT DEFAULT '', status TEXT NOT NULL DEFAULT 'pending',
        requested_by TEXT NOT NULL, received_at TEXT,
        FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
    );
    CREATE INDEX idx_orders_item ON orders(item_id);
    CREATE TABLE IF NOT EXISTS kpis (
        id INTEGER PRIMARY KEY AUTOINCREMENT, year INTEGER NOT NULL, month INTEGER NOT NULL,
        total_orders INTEGER DEFAULT 0, total_qty_ordered INTEGER DEFAULT 0, total_qty_received INTEGER DEFAULT 0,
        total_counted INTEGER DEFAULT 0, total_opening INTEGER DEFAULT 0, total_received_all INTEGER DEFAULT 0,
        total_used_all INTEGER DEFAULT 0, total_ending_all INTEGER DEFAULT 0, stockout_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    if db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        db.executemany("INSERT INTO users (name, role, phone) VALUES (?, ?, ?)",
                       [("Manager", "admin", "0900000001"),
                        ("Head Kitchen", "kitchen", "0900000002"),
                        ("Senior Cafe'", "cafe", "0900000003")])

    items = parse_excel(EXCEL_PATH)
    print(f"Read {len(items)} items from Excel")
    db.executemany("""
        INSERT OR REPLACE INTO items (code, name, unit, category, opening, received, used, ending, par, status, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Main Store', datetime('now'))
    """, items)
    db.commit()
    db.close()
    print("✅ Database created:", DB_PATH)

if __name__ == "__main__":
    main()
