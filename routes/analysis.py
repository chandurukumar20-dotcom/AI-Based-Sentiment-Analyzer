import os
import uuid
from datetime import datetime
from pathlib import Path
from flask import (
    render_template,
    request,
    jsonify,
    send_file,
    current_app,
    abort
)
from werkzeug.utils import secure_filename
import pandas as pd
from . import analysis_bp
from database.db import get_db
from models.sentiment_model import get_analyzer
from config import Config


def allowed_file(filename: str) -> bool:
    """Checks if uploaded file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def detect_text_column(df: pd.DataFrame, user_specified_col: str = None) -> str:
    """
    Intelligently identifies the review or text column in the DataFrame.
    """
    if user_specified_col and user_specified_col in df.columns:
        return user_specified_col

    # Common candidates for sentiment text
    candidates = [
        "review_text", "review", "text", "customer_review", "feedback",
        "comment", "comments", "content", "body", "message", "reviews",
        "description", "sentence", "tweet"
    ]
    cols_lower = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate in cols_lower:
            return cols_lower[candidate]

    # Find first column with string/object dtype
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            return col

    # Fallback to first column
    return df.columns[0] if len(df.columns) > 0 else None


@analysis_bp.route("/analyze")
def analyze_view():
    """Renders the single text analysis page."""
    analyzer = get_analyzer()
    db = get_db()
    return render_template(
        "analyze.html",
        analyzer=analyzer,
        db_status=db.get_status()
    )


@analysis_bp.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    API endpoint for single text sentiment analysis.
    Payload: { "text": "...", "save": true }
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    save_record = data.get("save", True)

    if not text:
        return jsonify({
            "success": False,
            "error": "Please enter some text or customer review to analyze."
        }), 400

    if len(text) > 10000:
        return jsonify({
            "success": False,
            "error": "Text exceeds the maximum length limit of 10,000 characters."
        }), 400

    analyzer = get_analyzer()
    result = analyzer.analyze_text(text)

    # Save to database if requested
    saved_record = None
    if save_record:
        db = get_db()
        saved_record = db.insert_record(
            text=text,
            sentiment=result["sentiment"],
            confidence=result["confidence"],
            scores=result["scores"],
            source="single"
        )

    return jsonify({
        "success": True,
        "data": {
            "text": text,
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
            "compound": result["compound"],
            "scores": result["scores"],
            "preprocessing": result["preprocessing"],
            "engine": result.get("engine", analyzer.engine_name),
            "record_id": saved_record.get("_id") if saved_record else None
        }
    })


@analysis_bp.route("/bulk-analysis")
@analysis_bp.route("/bulk")
def bulk_analysis_view():
    """Renders the Batch / Bulk CSV analysis page."""
    analyzer = get_analyzer()
    db = get_db()
    return render_template(
        "bulk_analysis.html",
        analyzer=analyzer,
        db_status=db.get_status()
    )


@analysis_bp.route("/api/bulk-analyze", methods=["POST"])
def api_bulk_analyze():
    """
    Handles CSV file upload, processes sentiment for each row,
    stores batch records in database, and generates downloadable CSV.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part in the upload request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file format. Please upload a .csv file."}), 400

    save_to_db = request.form.get("save_to_db", "true").lower() in ("true", "1", "yes")
    custom_col = request.form.get("text_column", "").strip() or None

    try:
        # Read uploaded CSV with pandas
        try:
            df = pd.read_csv(file)
        except Exception:
            file.seek(0)
            df = pd.read_csv(file, encoding="latin1")

        if df.empty:
            return jsonify({"success": False, "error": "The uploaded CSV file contains no data."}), 400

        # Detect column to analyze
        target_col = detect_text_column(df, custom_col)
        if not target_col or target_col not in df.columns:
            return jsonify({
                "success": False,
                "error": "Could not identify a text/review column. Available columns: " + ", ".join(df.columns)
            }), 400

        # Limit to 10,000 rows per batch for safety
        max_batch_size = 10000
        if len(df) > max_batch_size:
            df = df.iloc[:max_batch_size]

        analyzer = get_analyzer()
        db = get_db()

        sentiments = []
        confidences = []
        compounds = []
        pos_scores = []
        neg_scores = []
        neu_scores = []
        db_records = []

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        ts = datetime.utcnow().timestamp()
        orig_filename = secure_filename(file.filename)

        for _, row in df.iterrows():
            val = row[target_col]
            text = str(val) if pd.notna(val) else ""
            res = analyzer.analyze_text(text)

            sentiments.append(res["sentiment"])
            confidences.append(res["confidence"])
            compounds.append(res["compound"])
            pos_scores.append(res["scores"]["positive"])
            neg_scores.append(res["scores"]["negative"])
            neu_scores.append(res["scores"]["neutral"])

            if save_to_db and text.strip():
                db_records.append({
                    "text": text[:500],  # store reasonable snippet
                    "sentiment": res["sentiment"],
                    "confidence": res["confidence"],
                    "scores": res["scores"],
                    "source": "batch",
                    "filename": orig_filename,
                    "created_at": now_str,
                    "timestamp": ts
                })

        # Attach sentiment results to DataFrame
        df["Predicted_Sentiment"] = sentiments
        df["Confidence_Score"] = confidences
        df["Compound_Score"] = compounds
        df["Positive_Score"] = pos_scores
        df["Negative_Score"] = neg_scores
        df["Neutral_Score"] = neu_scores

        # Save to database in batch
        if save_to_db and db_records:
            db.insert_many_records(db_records)

        # Generate output CSV file
        out_token = f"analyzed_{int(ts)}_{uuid.uuid4().hex[:8]}.csv"
        out_filepath = Config.UPLOAD_FOLDER / out_token
        df.to_csv(out_filepath, index=False)

        # Calculate batch statistics
        total = len(df)
        pos_c = sum(1 for s in sentiments if s == "Positive")
        neg_c = sum(1 for s in sentiments if s == "Negative")
        neu_c = sum(1 for s in sentiments if s == "Neutral")
        avg_conf = round(sum(confidences) / total, 1) if total > 0 else 0.0

        # Create preview of first 30 rows
        preview_cols = [col for col in df.columns if col not in ("Compound_Score", "Positive_Score", "Negative_Score", "Neutral_Score")]
        preview_data = df[preview_cols].head(30).to_dict(orient="records")

        return jsonify({
            "success": True,
            "filename": orig_filename,
            "download_token": out_token,
            "analyzed_column": target_col,
            "total_records": total,
            "summary": {
                "total": total,
                "positive": pos_c,
                "negative": neg_c,
                "neutral": neu_c,
                "positive_pct": round(pos_c / total * 100, 1) if total > 0 else 0.0,
                "negative_pct": round(neg_c / total * 100, 1) if total > 0 else 0.0,
                "neutral_pct": round(neu_c / total * 100, 1) if total > 0 else 0.0,
                "avg_confidence": avg_conf
            },
            "columns": list(df.columns),
            "preview": preview_data
        })

    except Exception as exc:
        current_app.logger.error(f"Error during bulk analysis: {exc}")
        return jsonify({
            "success": False,
            "error": f"Failed to analyze CSV file: {str(exc)}"
        }), 500


@analysis_bp.route("/download-results/<filename>")
def download_results(filename: str):
    """Downloads the analyzed CSV file."""
    safe_name = secure_filename(filename)
    file_path = Config.UPLOAD_FOLDER / safe_name
    if not file_path.exists():
        abort(404, description="Result file not found or expired.")

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"sentiment_analysis_results_{safe_name}",
        mimetype="text/csv"
    )


@analysis_bp.route("/download-sample-csv")
def download_sample_csv():
    """Provides the pre-bundled sample reviews CSV file."""
    sample_path = Config.BASE_DIR / "sample_data" / "sample_reviews.csv"
    if not sample_path.exists():
        abort(404, description="Sample dataset not found.")

    return send_file(
        sample_path,
        as_attachment=True,
        download_name="sample_customer_reviews.csv",
        mimetype="text/csv"
    )
