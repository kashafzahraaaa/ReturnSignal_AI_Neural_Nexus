
import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory

from classifier import classify_complaint
from analyzer import analyze_records, root_cause_analysis


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "returnsignal.db")

app = Flask(
    __name__,
    static_folder=BASE_DIR,
    static_url_path=""
)

os.makedirs(DATA_DIR, exist_ok=True)


# Product categories selected by customers.
PRODUCT_CATEGORIES = [
    "Cosmetics & Beauty",
    "Electronics",
    "Clothing & Fashion",
    "Home Appliances",
    "Kitchenware & Utensils",
    "Furniture & Home Decor",
    "Food & Beverages",
    "Health & Personal Care",
    "Toys & Games",
    "Books & Stationery",
    "Sports & Fitness",
    "Other Product Category",
    "Unknown / Uncategorized"
]


# Complaint categories assigned by AI or human reviewers.
COMPLAINT_CATEGORIES = [
    "Damaged Product",
    "Leakage / Spillage",
    "Missing Items / Parts",
    "Wrong Product Delivered",
    "Poor Product Quality",
    "Defective / Not Working",
    "Damaged Packaging",
    "Expired Product",
    "Incorrect Product Description",
    "Wrong Size / Quantity",
    "Delivery Delay",
    "Incorrect Delivery",
    "Return / Refund Issue",
    "Other / New Complaint",
    "Unknown / Uncategorized"
]


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as db:

        # Create the complaints table if it does not already exist.
        db.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT,
                date TEXT,
                product TEXT,
                complaint_text TEXT,
                category TEXT,
                confidence REAL,
                status TEXT,
                severity TEXT,
                explanation TEXT,
                corrected INTEGER DEFAULT 0
            )
        """)

        # Safely add product_category to an existing database.
        # Existing complaint records are preserved.
        columns = [
            row["name"]
            for row in db.execute(
                "PRAGMA table_info(complaints)"
            ).fetchall()
        ]

        if "product_category" not in columns:
            db.execute("""
                ALTER TABLE complaints
                ADD COLUMN product_category TEXT
                DEFAULT 'Unknown / Uncategorized'
            """)

        db.commit()


def row_to_dict(row):
    return dict(row)


def get_records():
    with get_connection() as db:
        rows = db.execute(
            "SELECT * FROM complaints ORDER BY id DESC"
        ).fetchall()

    return [row_to_dict(row) for row in rows]


def save_complaint(data):
    text = str(data.get("complaint_text", "") or "").strip()
    product = str(data.get("product", "") or "").strip()
    product_category = str(
        data.get("product_category", "") or ""
    ).strip()

    date = str(
        data.get("date", "") or datetime.now().strftime("%Y-%m-%d")
    )

    severity = str(
        data.get("severity", "Medium") or "Medium"
    ).strip()

    complaint_id = str(
        data.get("complaint_id")
        or f"RS-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    )

    # AI automatically identifies the complaint category.
    result = classify_complaint(text)

    category = result["category"]
    confidence = result["confidence"]
    status = result["status"]
    explanation = result["explanation"]

    with get_connection() as db:
        cursor = db.execute("""
            INSERT INTO complaints
            (
                complaint_id,
                date,
                product,
                product_category,
                complaint_text,
                category,
                confidence,
                status,
                severity,
                explanation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id,
            date,
            product,
            product_category,
            text,
            category,
            confidence,
            status,
            severity,
            explanation
        ))

        db.commit()
        record_id = cursor.lastrowid

    return {
        "id": record_id,
        "complaint_id": complaint_id,
        "product": product,
        "product_category": product_category,
        "complaint_text": text,
        "date": date,
        "category": category,
        "severity": severity,
        "explanation": explanation,
        "confidence": confidence,
        "status": status
    }


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "application": "ReturnSignal AI"
    })


@app.route("/api/product-categories")
def product_categories():
    return jsonify(PRODUCT_CATEGORIES)


@app.route("/api/complaint-categories")
def complaint_categories():
    return jsonify(COMPLAINT_CATEGORIES)


@app.route("/api/complaints", methods=["GET", "POST"])
def complaints():

    if request.method == "GET":
        return jsonify(get_records())

    data = request.get_json(silent=True) or {}

    complaint_text = str(
        data.get("complaint_text", "") or ""
    ).strip()

    product = str(
        data.get("product", "") or ""
    ).strip()

    product_category = str(
        data.get("product_category", "") or ""
    ).strip()

    if not complaint_text:
        return jsonify({
            "error": "Please enter a complaint description."
        }), 400

    if not product:
        return jsonify({
            "error": "Please enter a product name."
        }), 400

    if product_category not in PRODUCT_CATEGORIES:
        return jsonify({
            "error": "Please select a valid product category."
        }), 400

    severity = str(
        data.get("severity", "Medium") or "Medium"
    ).strip()

    if severity not in ["Low", "Medium", "High"]:
        return jsonify({
            "error": "Please select a valid severity."
        }), 400

    result = save_complaint(data)

    return jsonify(result), 201


@app.route("/api/analysis")
def analysis():
    records = get_records()

    summary = analyze_records(records)
    causes = root_cause_analysis(records)

    return jsonify({
        "summary": summary,
        "root_causes": causes,
        "records": records
    })


@app.route("/api/correct/<int:record_id>", methods=["POST"])
def correct(record_id):
    data = request.get_json(silent=True) or {}

    category = str(
        data.get("category", "")
    ).strip()

    if category not in COMPLAINT_CATEGORIES:
        return jsonify({
            "error": "Please choose a valid complaint category."
        }), 400

    with get_connection() as db:
        cursor = db.execute("""
            UPDATE complaints
            SET category = ?,
                status = 'verified',
                corrected = 1,
                explanation = ?
            WHERE id = ?
        """, (
            category,
            f"Category corrected and verified by a human reviewer: {category}.",
            record_id
        ))

        db.commit()

    if cursor.rowcount == 0:
        return jsonify({
            "error": "Complaint not found."
        }), 404

    return jsonify({
        "message": "Correction saved successfully.",
        "category": category
    })


initialize_database()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
