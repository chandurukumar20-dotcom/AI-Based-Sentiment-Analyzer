from flask import render_template, jsonify
from . import dashboard_bp
from database.db import get_db
from models.sentiment_model import get_analyzer


@dashboard_bp.route("/")
def home():
    """Renders the Home Page with project overview and highlights."""
    db = get_db()
    stats = db.get_statistics()
    analyzer = get_analyzer()
    return render_template("index.html", stats=stats, analyzer=analyzer, db_status=db.get_status())


@dashboard_bp.route("/dashboard")
def dashboard_view():
    """Renders the interactive Dashboard view with metrics and charts."""
    db = get_db()
    stats = db.get_statistics()
    db_status = db.get_status()
    analyzer = get_analyzer()
    return render_template("dashboard.html", stats=stats, db_status=db_status, analyzer=analyzer)


@dashboard_bp.route("/about")
def about():
    """Renders the About page explaining NLP methodology and tech stack."""
    analyzer = get_analyzer()
    db = get_db()
    return render_template("about.html", analyzer=analyzer, db_status=db.get_status())


@dashboard_bp.route("/api/stats")
def api_stats():
    """Returns real-time dashboard statistics in JSON format for Chart.js."""
    db = get_db()
    stats = db.get_statistics()
    return jsonify({
        "success": True,
        "data": stats
    })


@dashboard_bp.route("/api/system-status")
def system_status():
    """Returns database and NLP model connectivity status."""
    db = get_db()
    analyzer = get_analyzer()
    return jsonify({
        "success": True,
        "database": db.get_status(),
        "model": {
            "engine": analyzer.engine_name,
            "model_name": analyzer.model_name,
            "use_transformers": analyzer.use_transformers
        }
    })
