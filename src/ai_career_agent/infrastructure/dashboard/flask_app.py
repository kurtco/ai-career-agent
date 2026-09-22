from pathlib import Path

from flask import Flask, jsonify, render_template, request

from ai_career_agent.infrastructure.config import settings
from ai_career_agent.infrastructure.persistence.sqlite_repository import (
    SqliteOfferRepository,
)


def create_app() -> Flask:
    """Factory del servidor dashboard; como un AppModule de Nest con inyección manual."""
    template_dir = Path(__file__).parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))
    repository = SqliteOfferRepository(settings.db_path, settings.timezone)

    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    @app.route("/api/offers")
    def api_offers() -> dict:
        days = request.args.get("days", type=int)
        offers = repository.find_all(days=days)
        return jsonify(offers)

    @app.route("/api/offers/<offer_id>/applied", methods=["POST"])
    def api_applied(offer_id: str) -> dict:
        data = request.get_json(silent=True) or {}
        repository.update_applied(offer_id, bool(data.get("applied", False)))
        return jsonify({"ok": True})

    @app.route("/api/offers/<offer_id>/notes", methods=["POST"])
    def api_notes(offer_id: str) -> dict:
        data = request.get_json(silent=True) or {}
        repository.update_notes(offer_id, str(data.get("notes", "")))
        return jsonify({"ok": True})

    return app


def run_dashboard(host: str, port: int, debug: bool = False) -> None:
    """Punto de entrada síncrono del servidor Flask."""
    app = create_app()
    print(f"Dashboard disponible en http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
