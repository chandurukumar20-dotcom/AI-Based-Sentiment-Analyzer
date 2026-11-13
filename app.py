import os
import logging
from flask import Flask, render_template, jsonify
from config import Config
from routes import dashboard_bp, analysis_bp, history_bp
from database.db import get_db
from models.sentiment_model import get_analyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sentiment_app")


def create_app():
    """Application factory for Flask sentiment analysis web application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(history_bp)

    # Context processor to inject global state to all templates
    @app.context_processor
    def inject_global_data():
        db = get_db()
        analyzer = get_analyzer()
        return {
            "app_name": "SentiAI Pro",
            "db_status": db.get_status(),
            "model_engine": analyzer.engine_name
        }

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html", error=str(e)), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("500.html", error=str(e)), 500

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({
            "success": False,
            "error": "The uploaded file exceeds the 16MB file size limit."
        }), 413

    @app.route("/health")
    def health_check():
        db = get_db()
        analyzer = get_analyzer()
        return jsonify({
            "status": "healthy",
            "database": db.get_status(),
            "analyzer_engine": analyzer.engine_name
        })

    return app


app = create_app()

if __name__ == "__main__":
    db = get_db()
    analyzer = get_analyzer()
    db_info = db.get_status()

    print("\n" + "=" * 65)
    print("  [*] AI-Based Sentiment Analysis Web Application")
    print("=" * 65)
    print(f"  * Web URL     : http://127.0.0.1:{Config.PORT}")
    print(f"  * AI Model    : {analyzer.engine_name}")
    print(f"  * Database    : {db_info['storage_mode'].upper()} ({db_info['message']})")
    print(f"  * Stored Data : {db_info['total_records']} records")
    print("=" * 65 + "\n")

    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG
    )
