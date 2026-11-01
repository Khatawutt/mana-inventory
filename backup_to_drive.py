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
NETWORK_BACKUP_DIR = r"J:\ไดรฟ์ของฉัน\MANA Inventory Backups"

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

def backup_to_network_drive():
    r"""
    สำรองฐานข้อมูลไปยัง J:\ไดรฟ์ของฉัน\MANA Inventory Backups
    """
    if not os.path.exists(NETWORK_BACKUP_DIR):
        try:
            os.makedirs(NETWORK_BACKUP_DIR, exist_ok=True)
        except Exception as e:
            print(f"❌ ไม่สามารถสร้างโฟลเดอร์ backup ได้: {e}")
            return False
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"mana_inventory_backup_{timestamp}.db"
    dest_path = os.path.join(NETWORK_BACKUP_DIR, backup_name)
    
    try:
        shutil.copy2(DB_PATH, dest_path)
        print(f"✅ สำรองไปยัง J:\\ไดรฟ์ของฉัน\\MANA Inventory Backups เรียบร้อย")
        print(f"   ตำแหน่ง: {dest_path}")
        return True
    except Exception as e:
        print(f"❌ สำรองไม่สำเร็จ: {e}")
        return False


def main():
    print("=" * 50)
    print("MANA Garden - สำรองฐานข้อมูล")
    print("=" * 50)
    
    # สำรองในเครื่องก่อนเสมอ
    print("\n1. สำรองในเครื่อง...")
    backup_local()
    
    # สำรองไป J:\ไดรฟ์ของฉัน\MANA Inventory Backups
    print("\n2. สำรองไปยัง J:\\ไดรฟ์ของฉัน\\MANA Inventory Backups...")
    if backup_to_network_drive():
        print("✅ สำรองข้อมูลครบถ้วน")
    else:
        print("⚠️  สำรองเฉพาะในเครื่องเท่านั้น")

if __name__ == "__main__":
    main()
