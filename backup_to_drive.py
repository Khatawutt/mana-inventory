"""
backup_to_drive.py
สำรองฐานข้อมูล SQLite ไปยัง Google Drive
- วิธีที่ 1: ใช้ Google Drive API (ต้องการ OAuth setup)
- วิธีที่ 2: คัดลอกไปที่โฟลเดอร์ที่ซิงค์กับ Google Drive (ง่ายขึ้น)
"""

import sqlite3
import os
import shutil
import datetime
from pathlib import Path

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "mana_inventory.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
GDRIVE_SYNC_FOLDER = r"C:\Users\Khatawutt's PC\Google Drive"  # ปรับตามโฟลเดอร์จริงของคุณ

def backup_local():
    """สำรองฐานข้อมูลไปที่โฟลเดอร์ backups ในโปรเจกต์"""
    if not os.path.exists(DB_PATH):
        print(f"ไม่พบฐานข้อมูล: {DB_PATH}")
        return False
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"mana_inventory_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    shutil.copy2(DB_PATH, backup_path)
    print(f"✅ สำรองฐานข้อมูลเรียบร้อย: {backup_path}")
    return True

def backup_to_gdrive_sync():
    """
    สำรองฐานข้อมูลไปที่โฟลเดอร์ที่ซิงค์กับ Google Drive
    วิธีนี้不需要 OAuth - แค่ต้องมี Google Drive for Desktop ติดตั้งอยู่
    """
    # ลองหาหน้าโฟลเดอร์ Google Drive ที่แตกต่างกัน
    possible_paths = [
        r"C:\Users\Khatawutt's PC\Google Drive",
        r"C:\Users\Khatawutt's PC\GoogleDrive",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Drive\My Drive"),
        os.path.expandvars(r"%APPDATA%\Google\Drive\My Drive"),
    ]
    
    gdrive_path = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            gdrive_path = path
            break
    
    if not gdrive_path:
        print("⚠️  ไม่พบโฟลเดอร์ Google Drive")
        print("   กรุณาติดตั้ง Google Drive for Desktop หรือใช้วิธีสำรองในเครื่อง")
        return False
    
    # สร้างโฟลเดอร์สำหรับ backup ใน Google Drive
    dest_folder = os.path.join(gdrive_path, "MANA Inventory Backups")
    os.makedirs(dest_folder, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"mana_inventory_backup_{timestamp}.db"
    dest_path = os.path.join(dest_folder, backup_name)
    
    shutil.copy2(DB_PATH, dest_path)
    print(f"✅ สำรองไปยัง Google Drive เรียบร้อย")
    print(f"   ตำแหน่ง: {dest_path}")
    return True

def backup_to_gdrive_api():
    """
    สำรองฐานข้อมูลผ่าน Google Drive API (ต้องการ OAuth setup)
    ตรวจสอบว่า google-workspace skill ตั้งค่าแล้ว
    """
    try:
        import sys
        skill_dir = os.path.expanduser("~/.hermes/skills/productivity/google-workspace/scripts")
        if not os.path.exists(os.path.join(skill_dir, "google_api.py")):
            print("ไม่พบ google-workspace skill")
            return False
        sys.path.insert(0, skill_dir)
        import google_api
    except ImportError as e:
        print(f"ไม่พบ google-workspace skill: {e}")
        return False
    
    try:
        result = google_api.GoogleAPI().drive.upload(
            DB_PATH,
            name="mana_inventory_backup.db",
            parent=None
        )
    except Exception as e:
        print(f"อัปโหลดไม่สำเร็จ: {e}")
        return False
    
    if result.get("status") == "uploaded":
        print(f"อัปโหลดไปยัง Google Drive เรียบร้อย")
        return True
    else:
        print(f"อัปโหลดไม่สำเร็จ: {result}")
        return False

def main():
    print("=" * 50)
    print("MANA Garden - สำรองฐานข้อมูล")
    print("=" * 50)
    
    # สำรองในเครื่องก่อนเสมอ
    print("\n1. สำรองในเครื่อง...")
    backup_local()
    
    # ลองสำรองไป Google Drive
    print("\n2. สำรองไปยัง Google Drive...")
    if backup_to_gdrive_sync():
        print("✅ สำรองข้อมูลครบถ้วน")
    else:
        print("⚠️  สำรองเฉพาะในเครื่องเท่านั้น")
        print("   Tip: ติดตั้ง Google Drive for Desktop เพื่อซิงค์อัตโนมัติ")

if __name__ == "__main__":
    main()
