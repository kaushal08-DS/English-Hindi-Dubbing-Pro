from flask import Flask
from .config import load_config

def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    load_config(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app
