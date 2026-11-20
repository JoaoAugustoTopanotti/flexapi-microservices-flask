from flask import Blueprint, jsonify, request

import regras
from regras import ErroRegra

bp = Blueprint("planos", __name__)


@bp.errorhandler(ErroRegra)
def tratar_erro(e):
    return jsonify({"erro": e.mensagem}), e.status


@bp.get("/")
def status():
    return jsonify({"servico": "planos", "status": "ok"})


@bp.get("/planos")
def listar():
    return jsonify(regras.listar())


@bp.get("/planos/<int:plano_id>")
def buscar(plano_id):
    return jsonify(regras.buscar(plano_id).to_dict())


@bp.post("/planos")
def criar():
    plano = regras.criar(request.get_json(silent=True))
    return jsonify(plano.to_dict()), 201


@bp.put("/planos/<int:plano_id>")
def atualizar(plano_id):
    plano = regras.atualizar(plano_id, request.get_json(silent=True))
    return jsonify(plano.to_dict())


@bp.delete("/planos/<int:plano_id>")
def remover(plano_id):
    regras.remover(plano_id)
    return jsonify({"mensagem": f"Plano {plano_id} removido."})
