import openpyxl

EXCEL_PATH = r"C:\Users\Khatawutt's PC\AppData\Local\hermes\attachments\ระบบ Inventory MANA Garden (Master System) - Linked.xlsx"
wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)

# ดู Kitchen Master
ws = wb.worksheets[0]
rows = list(ws.iter_rows(values_only=True))
header_idx = None
for i, row in enumerate(rows):
    if row and any(c and str(c).strip().upper() == 'CODE' for c in row):
        header_idx = i
        break
print("Header:", rows[header_idx])
print()
# ดู data 20 ตัวแรก
for row in rows[header_idx+1:header_idx+25]:
    print(row)
