import os

from flask import Flask

from config import Config


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )
    app.config.from_object(Config)
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.jobs import bp as jobs_bp
    from app.blueprints.applications import bp as applications_bp
    from app.blueprints.ranking import bp as ranking_bp
    from app.blueprints.pages import bp as pages_bp
    from app.blueprints.admin import bp as admin_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(ranking_bp, url_prefix="/api/ranking")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(pages_bp)

    return app
