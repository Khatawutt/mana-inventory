"""
seed_real_items.py
Seed รายการ Inventory จริงของ MANA Garden ลง mana_inventory.db
- อัปเดตข้อมูลเดิม (INSERT OR REPLACE) โดยไม่ลบ users / kpi / orders / counts
- ใช้ unit ที่ใช้งานจริงในครัวและคาเฟ่
"""

import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "mana_inventory.db")

ITEMS = [
    # kitchen
    ("K001", "น้ำมันพืช",        "L",   "kitchen", 6, 0, 0, 4,  4,  "ปกติ"),
    ("K002", "น้ำมันมะกอก",      "L",   "kitchen", 2, 0, 0, 1,  1,  "ปกติ"),
    ("K003", "เกลือ",            "kg",  "kitchen", 5, 0, 0, 2,  2,  "ปกติ"),
    ("K004", "น้ำตาล",           "kg",  "kitchen", 4, 0, 0, 2,  2,  "ปกติ"),
    ("K005", "พริกไทยดำ",        "g",   "kitchen", 50,0, 0, 20,20, "ปกติ"),
    ("K006", "กระเทียม",         "head","kitchen", 20,0, 0, 10,10,"ปกติ"),
    ("K007", "หัวหอม",           "head","kitchen", 15,0, 0, 8, 8, "ปกติ"),
    ("K008", "หอมแดง",           "kg",  "kitchen", 2, 0, 0, 1, 1, "ปกติ"),
    ("K009", "ร voix ผัก",        "kg",  "kitchen", 8, 0, 0, 4, 4, "ปกติ"),
    ("K010", "ผักกาดหอม",        "kg",  "kitchen", 3, 0, 0, 2, 2, "ปกติ"),
    ("K011", "ต้นหอม",           "kg",  "kitchen", 2, 0, 0, 1, 1, "ปกติ"),
    ("K012", "กระเจี๊ยบ",        "kg",  "kitchen", 1, 0, 0, 1, 1, "ปกติ"),
    ("K013", "ใบเตย",             "pcs", "kitchen", 50,0, 0, 20,20,"ปกติ"),
    ("K014", "น้ำปลา",            "L",   "kitchen", 3, 0, 0, 2, 2, "ปกติ"),
    ("K015", "ซีอิ้วขาว",         "L",   "kitchen", 2, 0, 0, 1, 1, "ปกติ"),
    ("K016", "ซอสหอย",           "L",   "kitchen", 1, 0, 0, 1, 1, "ปกติ"),
    ("K017", "เนย",               "kg",  "kitchen", 3, 0, 0, 2, 2, "ปกติ"),
    ("K018", "ไข่",               "tray","kitchen", 5, 0, 0, 3, 3, "ปกติ"),
    ("K019", "ขนมปัง",            "pcs", "kitchen", 20,0, 0, 10,10,"ปกติ"),
    ("K020", "นมสด",             "L",   "kitchen", 6, 0, 0, 3, 3, "ปกติ"),
    # cafe
    ("C001", "เมล็ดกาแฟ Arabica","kg",  "cafe",    2, 0, 0, 1, 1, "ปกติ"),
    ("C002", "กาแฟผสม",          "kg",  "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C003", "ผงชาเขียว",         "kg",  "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C004", "ไซรัป tutti-frutti","L",  "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C005", "ไซรัป Ginger",      "L",   "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C006", "ไซรัป Pandan",      "L",   "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C007", "น้ำไซรัป Light",    "L",   "cafe",    2, 0, 0, 1, 1, "ปกติ"),
    ("C008", "น้ำโซดา",           "L",   "cafe",    4, 0, 0, 2, 2, "ปกติ"),
    ("C009", "น้ำดื่ม",            "L",   "cafe",    6, 0, 0, 3, 3, "ปกติ"),
    ("C010", "น้ำแข็ง",            "kg",  "cafe",    10,0, 0, 5, 5, "ปกติ"),
    ("C011", "นมข้นหวาน",         "L",   "cafe",    2, 0, 0, 1, 1, "ปกติ"),
    ("C012", "นมสด UHT",         "L",   "cafe",    2, 0, 0, 1, 1, "ปกติ"),
    ("C013", "ผงโกโก้",           "kg",  "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C014", "กลิ่นวานิลลา",       "ml",  "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C015", "กลิ่นอัลมอนด์",      "ml",  "cafe",    1, 0, 0, 1, 1, "ปกติ"),
    ("C016", "แก้ว Plastic",      "pcs", "cafe",    100,0,0,50,50,"ปกติ"),
    ("C017", "ฝา duly",           "pcs", "cafe",    80, 0,0,40,40,"ปกติ"),
    ("C018", "ไม้ Stirrer",       "pcs", "cafe",    200,0,0,100,100,"ปกติ"),
]

def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"ไม่พบฐานข้อมูล: {DB_PATH}")

    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON")

    sql = """
        INSERT OR REPLACE INTO items
            (code, name, unit, category, opening, received, used, ending, par, status, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Main Store', ?)
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [(c, n, u, cat, o, r, u2, e, p, s, now) for c, n, u, cat, o, r, u2, e, p, s in ITEMS]

    db.executemany(sql, rows)
    db.commit()

    total = db.execute("SELECT COUNT(*) FROM items").fetchone()[0]
    db.close()
    print(f"Seed เรียบร้อยครับ — รวม {total} รายการในระบบ")

if __name__ == "__main__":
    main()
