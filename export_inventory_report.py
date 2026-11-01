"""
export_inventory_report.py
ส่งออกรายงาน Inventory เป็น Excel
"""
import sqlite3
import os
from datetime import datetime

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError:
    print("กรุณาติดตั้ง openpyxl: pip install openpyxl")
    exit(1)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "mana_inventory.db")
OUT_PATH = os.path.join(BASE_DIR, f"รายงาน_Inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")

def main():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"ไม่พบฐานข้อมูล: {DB_PATH}")

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    wb = openpyxl.Workbook()

    # ── Sheet 1: สต็อกปัจจุบัน ──
    ws1 = wb.active
    ws1.title = "สต็อกปัจจุบัน"
    headers1 = ["รหัส", "ชื่อสินค้า", "หน่วย", "หมวด", "ยอดยกมา", "รับเข้า", "จ่ายออก", "คงเหลือ", "จุดสั่งซื้อ", "สถานะ", "สถานที่"]
    ws1.append(headers1)
    for cell in ws1[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.alignment = Alignment(horizontal="center")

    rows = db.execute("SELECT * FROM items ORDER BY category, code").fetchall()
    for r in rows:
        ws1.append([
            r["code"], r["name"], r["unit"], r["category"],
            r["opening"], r["received"], r["used"], r["ending"],
            r["par"], r["status"], r["location"]
        ])

    # ── Sheet 2: รายการสั่งซื้อ ──
    ws2 = wb.create_sheet("รายการสั่งซื้อ")
    headers2 = ["เลขที่", "รหัส", "ชื่อสินค้า", "จำนวน", "หน่วย", "สถานะ", "วันที่ขอ", "ผู้ขอ"]
    ws2.append(headers2)
    for cell in ws2[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="70AD47")
        cell.alignment = Alignment(horizontal="center")

    orders = db.execute("""
        SELECT o.id, i.code, i.name, o.qty, i.unit, o.status, o.created_at, o.requested_by
        FROM orders o JOIN items i ON i.id = o.item_id
        ORDER BY o.created_at DESC
    """).fetchall()
    for o in orders:
        ws2.append([
            o["id"], o["code"], o["name"], o["qty"], o["unit"],
            o["status"], o["created_at"], o["requested_by"]
        ])

    # ── Sheet 3: ประวัติการนับ ──
    ws3 = wb.create_sheet("ประวัติการนับ")
    headers3 = ["วันที่", "รหัส", "ชื่อสินค้า", "หน่วย", "จำนวนนับ", "ผู้นับ", "สถานที่", "หมายเหตุ"]
    ws3.append(headers3)
    for cell in ws3[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="ED7D31")
        cell.alignment = Alignment(horizontal="center")

    counts = db.execute("""
        SELECT c.count_date, i.code, i.name, i.unit, c.physical_qty, c.counted_by, c.location, c.note
        FROM counts c JOIN items i ON i.id = c.item_id
        ORDER BY c.count_date DESC, c.id DESC
    """).fetchall()
    for c in counts:
        ws3.append([
            c["count_date"], c["code"], c["name"], c["unit"],
            c["physical_qty"], c["counted_by"], c["location"], c["note"]
        ])

    # ปรับความกว้างคอลัมน์
    for ws in [ws1, ws2, ws3]:
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column].width = adjusted_width

    wb.save(OUT_PATH)
    db.close()
    print(f"✅ ส่งออกรายงานเรียบร้อยครับ")
    print(f"   ไฟล์: {OUT_PATH}")

if __name__ == "__main__":
    main()
