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
        """Lista paginada y filtrada de ofertas para el dashboard."""
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=10, type=int)
        days = request.args.get("days", type=int)
        remote_only = request.args.get("remote_only", default="false").lower() == "true"
        full_time_only = request.args.get("full_time_only", default="false").lower() == "true"
        hide_applied = request.args.get("hide_applied", default="false").lower() == "true"
        search = request.args.get("search", default="", type=str)

        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 10
        if per_page > 200:
            per_page = 200

        offers, total = repository.find_filtered(
            days=days if days and days > 0 else None,
            remote_only=remote_only,
            full_time_only=full_time_only,
            hide_applied=hide_applied,
            search=search,
            limit=per_page,
            offset=(page - 1) * per_page,
        )
        return jsonify(
            {
                "offers": offers,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
            }
        )

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
