import logging
import os

from flask import Flask, request

from models import db
from regras import popular_dados_iniciais
from rotas import bp

SERVICO = "instrutores"
PORTA = 5003

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s | %(levelname)-7s | {SERVICO} | %(message)s",
)
log = logging.getLogger(SERVICO)


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///instrutores.db")
    app.json.ensure_ascii = False
    db.init_app(app)
    app.register_blueprint(bp)

    @app.after_request
    def registrar_requisicao(resposta):
        log.info("%s %s -> %s", request.method, request.path, resposta.status_code)
        return resposta

    with app.app_context():
        db.create_all()
        popular_dados_iniciais()
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", PORTA)), debug=True)
