import io
from flask import (
    render_template,
    request,
    jsonify,
    Response
)
import pandas as pd
from . import history_bp
from database.db import get_db
from models.sentiment_model import get_analyzer


@history_bp.route("/history")
def history_view():
    """Renders the analysis history view."""
    db = get_db()
    analyzer = get_analyzer()
    stats = db.get_statistics()
    return render_template(
        "history.html",
        db_status=db.get_status(),
        stats=stats,
        analyzer=analyzer
    )


@history_bp.route("/api/history")
def api_get_history():
    """
    JSON API for history search, filtering, and pagination.
    Query params:
      - sentiment: 'all' | 'positive' | 'negative' | 'neutral'
      - search: string query
      - limit: integer max records
    """
    db = get_db()
    sentiment = request.args.get("sentiment", "all").strip()
    search = request.args.get("search", "").strip()
    limit = int(request.args.get("limit", 200))

    records = db.get_all_records(limit=limit, sentiment_filter=sentiment, search_query=search)

    return jsonify({
        "success": True,
        "count": len(records),
        "total_in_db": db.get_count(),
        "records": records
    })


@history_bp.route("/api/history/delete/<record_id>", methods=["POST", "DELETE"])
def api_delete_record(record_id: str):
    """Deletes an individual history record by ID."""
    db = get_db()
    deleted = db.delete_record(record_id)
    if deleted:
        return jsonify({
            "success": True,
            "message": "Record deleted successfully."
        })
    return jsonify({
        "success": False,
        "error": "Record not found or could not be deleted."
    }), 404


@history_bp.route("/api/history/clear", methods=["POST"])
def api_clear_history():
    """Clears all records from the database."""
    db = get_db()
    db.clear_all()
    return jsonify({
        "success": True,
        "message": "All history records have been cleared."
    })


@history_bp.route("/export-history")
def export_history_csv():
    """Generates and downloads a CSV export of all analysis history records."""
    db = get_db()
    records = db.get_all_records(limit=5000)

    if not records:
        # Return empty CSV with headers
        output = io.StringIO()
        output.write("ID,Created_At,Sentiment,Confidence_Pct,Source,Review_Text\n")
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=sentiment_history_empty.csv"}
        )

    # Format into DataFrame for clean CSV generation
    rows = []
    for r in records:
        scores = r.get("scores", {})
        rows.append({
            "ID": r.get("_id", ""),
            "Created_At": r.get("created_at", ""),
            "Sentiment": r.get("sentiment", ""),
            "Confidence_Pct": r.get("confidence", 0.0),
            "Source": r.get("source", "single"),
            "Positive_Score": scores.get("positive", 0.0),
            "Negative_Score": scores.get("negative", 0.0),
            "Neutral_Score": scores.get("neutral", 0.0),
            "Review_Text": r.get("text", "").replace("\n", " ").replace("\r", " ")
        })

    df = pd.DataFrame(rows)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    return Response(
        csv_buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=sentiment_analysis_history.csv"}
    )
