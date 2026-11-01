"""
MANA GARDEN — Restaurant Inventory System (Master System)
===========================================

- Frontend: HTML + CSS + Jinja2
- Backend: Flask (Python 3.14)
- Database: SQLite
- Run: python app.py  -> http://localhost:5000

Roles:
- ADMIN / Brand & Operation Manager : Dashboard KPI, Reports, approve orders
- KITCHEN / Head Kitchen : Inventory count, Order supply
- CAFE' / Senior Cafe' : Inventory count, Order supply
"""

import os
import sqlite3
import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, jsonify
)

# ── CONFIG ──
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "mana_inventory.db")
EXCEL_PATH = os.path.join(BASE_DIR, "ระบบ Inventory MANA Garden (Master System) - Linked.xlsx")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()
app.config["DB_PATH"] = DB_PATH
app.config["PORT"] = int(os.environ.get("PORT", 5000))


# ── DATABASE ──
def get_db():
    if "db" not in g:
        if not os.path.exists(DB_PATH):
            init_db()
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(SCHEMA)
    cur = db.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO users (name, role, phone) VALUES (?, ?, ?)",
            [("Manager", "admin", "0900000001"),
             ("Head Kitchen", "kitchen", "0900000002"),
             ("Senior Cafe'", "cafe", "0900000003")]
        )
    db.commit()
    db.close()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin','kitchen','cafe')),
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    unit TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    opening INTEGER DEFAULT 0,
    received INTEGER DEFAULT 0,
    used INTEGER DEFAULT 0,
    ending INTEGER DEFAULT 0,
    par INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ปกติ',
    location TEXT DEFAULT 'Main Store',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS counts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    location TEXT NOT NULL DEFAULT 'Main Store',
    counted_by TEXT NOT NULL,
    count_date TEXT NOT NULL,
    physical_qty INTEGER NOT NULL,
    note TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
CREATE INDEX idx_counts_item ON counts(item_id, count_date);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    qty INTEGER NOT NULL,
    unit_cost REAL DEFAULT 0,
    note TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    requested_by TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    received_at TEXT,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
CREATE INDEX idx_orders_item ON orders(item_id);
CREATE TABLE IF NOT EXISTS kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    total_orders INTEGER DEFAULT 0,
    total_qty_ordered INTEGER DEFAULT 0,
    total_qty_received INTEGER DEFAULT 0,
    total_counted INTEGER DEFAULT 0,
    total_opening INTEGER DEFAULT 0,
    total_received_all INTEGER DEFAULT 0,
    total_used_all INTEGER DEFAULT 0,
    total_ending_all INTEGER DEFAULT 0,
    stockout_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


# ── DECORATORS ──
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            flash("กรุณาเลือกบทบาทผู้ใช้ก่อนครับ", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

def role_required(*allowed_roles):
    def deco(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user" not in session:
                flash("กรุณาเลือกบทบาทผู้ใช้ก่อนครับ", "warning")
                return redirect(url_for("login"))
            if session.get("role") not in allowed_roles:
                flash("คุณไม่มีสิทธิ์เข้าถึงหน้านี้ครับ", "danger")
                return redirect(url_for("dashboard"))
            return f(*args, **kwargs)
        return wrapper
    return deco


# ── VIEWS ──
@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form.get("role", "").strip().lower()
        name = request.form.get("name", "").strip()
        if role in ("admin", "kitchen", "cafe") and name:
            session["user"] = name
            session["role"] = role
            flash(f"สวัสดี {name} ครับ (role: {role})", "success")
            return redirect(url_for("dashboard"))
        flash("บทบาทไม่ถูกต้องครับ กรุณาเลือก admin / kitchen / cafe", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("ออกจากระบบครับ", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    db = get_db()
    today = datetime.date.today()
    k = db.execute(
        "SELECT COUNT(*) as n FROM kpis WHERE year=? AND month=?",
        (today.year, today.month)
    ).fetchone()["n"]
    if k == 0:
        db.execute(
            """
            INSERT INTO kpis (year, month, total_orders, total_qty_ordered, total_qty_received,
                total_counted, total_opening, total_received_all, total_used_all,
                total_ending_all, stockout_count)
            SELECT ? as y, ? as m,
                (SELECT COUNT(*) FROM orders WHERE status!='cancelled') as total_orders,
                COALESCE((SELECT SUM(received) FROM items),0) as total_qty_ordered,
                COALESCE((SELECT SUM(used) FROM items),0) as total_qty_received,
                (SELECT COUNT(*) FROM counts WHERE strftime('%Y', count_date)=? AND strftime('%m', count_date)=?),
                COALESCE((SELECT SUM(opening) FROM items),0),
                COALESCE((SELECT SUM(received) FROM items),0),
                COALESCE((SELECT SUM(used) FROM items),0),
                COALESCE((SELECT SUM(ending) FROM items),0),
                (SELECT COUNT(*) FROM items WHERE status='ต้องสั่งซื้อ')
            """,
            (today.year, today.month, str(today.year), f"{today.month:02d}"),
        )
        db.commit()

    k = db.execute(
        "SELECT * FROM kpis WHERE year=? AND month=?", (today.year, today.month)
    ).fetchone()
    if not k:
        db.execute(
            """
            INSERT INTO kpis (year, month, total_orders, total_qty_ordered, total_qty_received,
                total_counted, total_opening, total_received_all, total_used_all,
                total_ending_all, stockout_count)
            SELECT ?, ?, 0,0,0,0,0,0,0,0,0
            """,
            (today.year, today.month),
        )
        db.commit()
        k = db.execute(
            "SELECT * FROM kpis WHERE year=? AND month=?", (today.year, today.month)
        ).fetchone()

    k = k or {
        "year": today.year, "month": today.month,
        "total_orders": 0, "total_qty_ordered": 0, "total_qty_received": 0,
        "total_counted": 0, "total_opening": 0, "total_received_all": 0,
        "total_used_all": 0, "total_ending_all": 0, "stockout_count": 0,
    }

    total_items = db.execute("SELECT COUNT(*) as n FROM items").fetchone()["n"]
    stockout_items = db.execute(
        "SELECT COUNT(*) as n FROM items WHERE status='ต้องสั่งซื้อ'"
    ).fetchone()["n"]
    high_value_items = db.execute(
        "SELECT code, name, ending, par FROM items WHERE ending <= par ORDER BY ending ASC LIMIT 5"
    ).fetchall()
    recent_orders = db.execute(
        """
        SELECT o.id, o.status, o.created_at, i.name, o.qty, o.requested_by
        FROM orders o JOIN items i ON i.id = o.item_id
        WHERE o.status IN ('pending','approved')
        ORDER BY o.created_at DESC LIMIT 10
        """
    ).fetchall()

    return render_template(
        "dashboard.html", kpi=k, total_items=total_items,
        stockout_items=stockout_items, high_value_items=high_value_items,
        recent_orders=recent_orders, today=today,
    )

@app.route("/kitchen")
@login_required
@role_required("kitchen", "admin")
def kitchen():
    db = get_db()
    low_items = db.execute(
        "SELECT * FROM items ORDER BY ending ASC"
    ).fetchall()
    cafe_items = db.execute(
        "SELECT * FROM items WHERE category='cafe' ORDER BY name"
    ).fetchall()
    return render_template(
        "kitchen.html", kitchen_items=low_items, cafe_items=cafe_items,
        current_role=session.get("role"), today=datetime.date.today(),
    )

@app.route("/cafe")
@login_required
@role_required("cafe", "admin")
def cafe():
    db = get_db()
    items = db.execute(
        "SELECT * FROM items WHERE category='cafe' ORDER BY name"
    ).fetchall()
    return render_template(
        "cafe.html", cafe_items=items, current_role=session.get("role"), today=datetime.date.today(),
    )

@app.route("/api/count", methods=["POST"])
@login_required
def api_count():
    data = request.get_json() or {}
    item_id = data.get("item_id")
    physical_qty = data.get("physical_qty")
    location = data.get("location", session.get("location", "Main Store"))
    note = data.get("note", "")

    if not item_id or not physical_qty:
        return jsonify({"success": False, "msg": "ข้อมูลไม่ครบครับ"}), 400

    db = get_db()
    try:
        db.execute(
            """
            INSERT INTO counts (item_id, location, counted_by, count_date, physical_qty, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (item_id, location, session["user"], datetime.date.today().isoformat(), physical_qty, note),
        )
        db.commit()

        db.execute(
            "UPDATE items SET ending = ? WHERE id = ?",
            (physical_qty, item_id),
        )
        db.execute(
            "UPDATE items SET status = CASE WHEN ? >= par THEN 'ปกติ' ELSE 'ต้องสั่งซื้อ' END WHERE id = ?",
            (physical_qty, item_id),
        )
        db.commit()

        db.execute(
            """
            INSERT INTO kpis (year, month, total_counted, created_at)
            VALUES (?, ?, 1, datetime('now'))
            ON CONFLICT(rowid) DO UPDATE SET total_counted = total_counted + 1
            """,
            (datetime.date.today().year, datetime.date.today().month),
        )
        db.commit()

        return jsonify({"success": True, "msg": "บันทึกการนับเรียบร้อยครับ"})
    except Exception as e:
        return jsonify({"success": False, "msg": str(e)}), 500

@app.route("/counts")
@login_required
@role_required("kitchen", "cafe", "admin")
def counts():
    db = get_db()
    item_id = request.args.get("item_id")
    location = request.args.get("location", "Main Store")
    count_date = request.args.get("count_date", datetime.date.today().isoformat())

    sql = """
        SELECT c.*, i.code, i.name, i.unit, i.par, i.ending as sys_qty
        FROM counts c JOIN items i ON i.id = c.item_id
        WHERE c.location = ? AND c.count_date = ?
    """
    params = [location, count_date]
    if item_id:
        sql += " AND c.item_id = ?"
        params.append(item_id)
    sql += " ORDER BY i.code"

    rows = db.execute(sql, params).fetchall()
    total = db.execute(
        "SELECT COUNT(*) as n FROM counts WHERE location=? AND count_date=?",
        (location, count_date),
    ).fetchone()["n"]

    return render_template(
        "counts.html", rows=rows, total=total, location=location, count_date=count_date,
        current_role=session.get("role"),
    )

@app.route("/order", methods=["GET", "POST"])
@login_required
@role_required("kitchen", "cafe", "admin")
def order():
    db = get_db()
    item_id = request.form.get("item_id")
    qty = request.form.get("qty", type=int)
    note = request.form.get("note", "").strip()

    if request.method == "POST" and item_id and qty:
        item = db.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
        if not item:
            flash("ไม่พบสินค้าครับ", "danger")
        elif qty <= 0:
            flash("จำนวนต้องมากกว่า 0 ครับ", "danger")
        else:
            db.execute(
                """
                INSERT INTO orders (item_id, qty, note, status, requested_by)
                VALUES (?, ?, ?, 'pending', ?)
                """,
                (item_id, qty, note, session["user"]),
            )
            db.commit()
            flash(f"สั่งของ {qty} x {item['name']} เรียบร้อยครับ (รออนุมัติ)", "success")
        return redirect(url_for("order"))

    roles = session.get("role")
    if roles == "kitchen":
        items = db.execute(
            "SELECT * FROM items WHERE category='kitchen' ORDER BY name"
        ).fetchall()
    elif roles == "cafe":
        items = db.execute(
            "SELECT * FROM items WHERE category='cafe' ORDER BY name"
        ).fetchall()
    else:
        items = db.execute("SELECT * FROM items ORDER BY name").fetchall()

    orders = db.execute(
        """
        SELECT o.id, o.status, o.qty, o.created_at, u.name as requested_by, i.code, i.name
        FROM orders o JOIN users u ON u.id = o.requested_by
        JOIN items i ON i.id = o.item_id
        WHERE o.status = 'pending'
        ORDER BY o.created_at DESC LIMIT 20
        """
    ).fetchall()

    return render_template(
        "order.html", items=items, orders=orders,
        current_role=session.get("role"),
    )

@app.route("/api/orders/<int:order_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_order(order_id):
    db = get_db()
    qty = request.form.get("qty", type=int) or request.json.get("qty")
    approved_by = session["user"]
    now = datetime.datetime.now().isoformat()

    db.execute(
        "UPDATE orders SET status='approved', approved_by=?, received_at=NULL WHERE id=?",
        (approved_by, order_id),
    )
    db.commit()
    return jsonify({"success": True, "msg": "อนุมัติเรียบร้อยครับ"})

@app.route("/api/orders/<int:order_id>/receive", methods=["POST"])
@login_required
@role_required("kitchen", "cafe", "admin")
def receive_order(order_id):
    db = get_db()
    db.execute(
        "UPDATE orders SET status='received', received_at=datetime('now') WHERE id=? AND status='approved'",
        (order_id,),
    )
    db.commit()
    return jsonify({"success": True, "msg": "บันทึกการรับของเรียบร้อยครับ"})

@app.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
@role_required("admin")
def cancel_order(order_id):
    db = get_db()
    db.execute(
        "UPDATE orders SET status='cancelled' WHERE id=? AND status='pending'",
        (order_id,),
    )
    db.commit()
    return jsonify({"success": True, "msg": "ยกเลิกเรียบร้อยครับ"})

@app.route("/reports")
@login_required
@role_required("admin")
def reports():
    db = get_db()
    today = datetime.date.today()
    period = request.args.get("period", "monthly")

    if period == "monthly":
        k = db.execute(
            """
            SELECT year, month, total_orders, total_qty_ordered, total_qty_received,
                total_counted, total_opening, total_received_all, total_used_all,
                total_ending_all, stockout_count
            FROM kpis WHERE year=? AND month=?
            ORDER BY year DESC, month DESC LIMIT 12
            """,
            (today.year, today.month),
        ).fetchall()
        title = f"รายงาน KPI รายเดือน — {today.strftime('%B %Y')}"
    else:
        k = db.execute("SELECT * FROM kpis ORDER BY id DESC LIMIT 1").fetchone()
        title = "รายงาน KPI ล่าสุด"

    stockouts = db.execute(
        "SELECT code, name, ending, par FROM items WHERE status='ต้องสั่งซื้อ' ORDER BY ending ASC"
    ).fetchall()
    opening_stock = db.execute(
        "SELECT code, name, unit, category, opening, received, used, ending, par FROM items WHERE opening > 0 ORDER BY category, code"
    ).fetchall()
    recent = db.execute(
        """
        SELECT o.id, o.qty, o.status, i.name, o.created_at
        FROM orders o JOIN items i ON i.id=o.item_id
        ORDER BY o.created_at DESC LIMIT 20
        """
    ).fetchall()
    counts = db.execute(
        """
        SELECT c.*, i.code, i.name, i.unit FROM counts c
        JOIN items i ON i.id=c.item_id
        ORDER BY c.count_date DESC, c.id DESC LIMIT 30
        """
    ).fetchall()

    return render_template(
        "reports.html", title=title, kpi_data=k, stockouts=stockouts,
        opening_stock=opening_stock, recent=recent, counts=counts, period=period, today=today,
    )

@app.route("/items")
@login_required
def items():
    db = get_db()
    cat = request.args.get("cat", "all")
    if cat == "kitchen":
        rows = db.execute(
            "SELECT * FROM items WHERE category='kitchen' ORDER BY name"
        ).fetchall()
    elif cat == "cafe":
        rows = db.execute(
            "SELECT * FROM items WHERE category='cafe' ORDER BY name"
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM items ORDER BY category, name"
        ).fetchall()
    return render_template(
        "items.html", items=rows, cat=cat, current_role=session.get("role"),
    )

if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
