import sys
import io
import json
from pathlib import Path

# Force UTF-8 encoding on standard output for Windows
if sys.platform.startswith("win"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from database.db import get_db

def run_tests():
    print("=" * 60)
    print("[*] Starting SentiAI Pro Automated Test Suite")
    print("=" * 60)

    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    # 1. Test HTML Pages
    pages = ["/", "/dashboard", "/analyze", "/bulk", "/history", "/about", "/health"]
    print("\n[Step 1] Testing Web Routes:")
    for path in pages:
        res = client.get(path)
        assert res.status_code == 200, f"Route {path} returned status {res.status_code}"
        print(f"  [OK] {path.ljust(15)} -> 200 OK")

    # 2. Test Benchmark Sentiment Predictions
    print("\n[Step 2] Testing Sentiment Analysis API with Benchmark Sentences:")
    test_cases = [
        {
            "text": "The product is excellent and the customer service is amazing.",
            "expected": "Positive"
        },
        {
            "text": "The product is terrible and I am very disappointed.",
            "expected": "Negative"
        },
        {
            "text": "The product was delivered yesterday.",
            "expected": "Neutral"
        }
    ]

    saved_ids = []
    for tc in test_cases:
        res = client.post(
            "/api/analyze",
            data=json.dumps({"text": tc["text"], "save": True}),
            content_type="application/json"
        )
        assert res.status_code == 200, f"Failed analyzing text: {tc['text']}"
        data = res.get_json()["data"]
        sentiment = data["sentiment"]
        confidence = data["confidence"]
        compound = data["compound"]
        saved_ids.append(data.get("record_id"))

        print(f"  Input   : \"{tc['text']}\"")
        print(f"  Result  : {sentiment} ({confidence}% confidence, compound: {compound})")
        assert sentiment == tc["expected"], f"Expected {tc['expected']}, got {sentiment}"
        print(f"  [OK] Prediction verified: matches {tc['expected']}\n")

    # 3. Test Statistics API
    print("[Step 3] Testing Statistics API (/api/stats):")
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.get_json()["data"]
    print(f"  [OK] Total: {stats['total']}, Pos: {stats['positive']}, Neg: {stats['negative']}, Neu: {stats['neutral']}")
    assert stats["total"] >= 3, "Total should have at least 3 records"

    # 4. Test History API and Filtering
    print("\n[Step 4] Testing History API (/api/history):")
    res = client.get("/api/history?sentiment=positive")
    assert res.status_code == 200
    pos_records = res.get_json()["records"]
    assert all(r["sentiment"] == "Positive" for r in pos_records), "Filtered records must all be Positive"
    print(f"  [OK] Positive sentiment filter verified ({len(pos_records)} records found)")

    # 5. Test Bulk CSV Analysis
    print("\n[Step 5] Testing Bulk CSV Analysis API (/api/bulk-analyze):")
    sample_csv_path = BASE_DIR / "sample_data" / "sample_reviews.csv"
    with open(sample_csv_path, "rb") as f:
        csv_bytes = f.read()

    res = client.post(
        "/api/bulk-analyze",
        data={
            "file": (io.BytesIO(csv_bytes), "sample_reviews.csv"),
            "save_to_db": "true"
        },
        content_type="multipart/form-data"
    )
    assert res.status_code == 200, f"Bulk analyze returned {res.status_code}: {res.data}"
    bulk_data = res.get_json()
    summary = bulk_data["summary"]
    print(f"  [OK] Bulk processed {bulk_data['total_records']} rows.")
    print(f"  [OK] Positive: {summary['positive']}, Negative: {summary['negative']}, Neutral: {summary['neutral']}")
    print(f"  [OK] Download Token: {bulk_data['download_token']}")

    # Test downloading the analyzed CSV
    download_res = client.get(f"/download-results/{bulk_data['download_token']}")
    assert download_res.status_code == 200
    assert b"Predicted_Sentiment" in download_res.data
    print(f"  [OK] Download enriched CSV verified ({len(download_res.data)} bytes)")

    # 6. Test Single Record Delete
    if saved_ids and saved_ids[0]:
        print(f"\n[Step 6] Testing Delete Record (/api/history/delete/{saved_ids[0]}):")
        del_res = client.post(f"/api/history/delete/{saved_ids[0]}")
        assert del_res.status_code == 200
        print(f"  [OK] Deleted record {saved_ids[0]} successfully")

    # 7. Test History CSV Export
    print("\n[Step 7] Testing History CSV Export (/export-history):")
    export_res = client.get("/export-history")
    assert export_res.status_code == 200
    assert b"Review_Text" in export_res.data
    print(f"  [OK] History CSV export verified ({len(export_res.data)} bytes)")

    print("\n" + "=" * 60)
    print("[SUCCESS] ALL TESTS PASSED SUCCESSFULLY! 100% FUNCTIONAL.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
