import os

from flask import Flask, jsonify

from app.database import init_db, close_db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=False)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE_PATH=os.environ.get("DATABASE_PATH", "instance/stocksense.db"),
        JWT_EXPIRES_MINUTES=int(os.environ.get("JWT_EXPIRES_MINUTES", "1440")),
        OTP_EXPIRES_MINUTES=int(os.environ.get("OTP_EXPIRES_MINUTES", "10")),
        DEBUG=os.environ.get("FLASK_DEBUG", "true").lower() == "true",
    )
    if test_config:
        app.config.update(test_config)

    init_db(app)
    app.teardown_appcontext(close_db)

    # ---- simple built-in CORS support (no external dependency needed) ----
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/api/<path:_any>", methods=["OPTIONS"])
    def cors_preflight(_any):
        return "", 204

    # ---------------------------------------------------------- blueprints
    from app.routes import (
        auth, products, settings, receipts, deliveries,
        transfers, adjustments, move_history, dashboard, profile,
    )

    app.register_blueprint(auth.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(receipts.bp)
    app.register_blueprint(deliveries.bp)
    app.register_blueprint(transfers.bp)
    app.register_blueprint(adjustments.bp)
    app.register_blueprint(move_history.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(profile.bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "StockSense IMS API"})

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500

    return app
