from flask import Blueprint, jsonify, request

import regras
from regras import ErroRegra

bp = Blueprint("instrutores", __name__)


@bp.errorhandler(ErroRegra)
def tratar_erro(e):
    return jsonify({"erro": e.mensagem}), e.status


@bp.get("/")
def status():
    return jsonify({"servico": "instrutores", "status": "ok"})


@bp.get("/instrutores")
def listar():
    return jsonify(regras.listar())


@bp.get("/instrutores/<int:instrutor_id>")
def buscar(instrutor_id):
    return jsonify(regras.buscar(instrutor_id).to_dict())


@bp.post("/instrutores")
def criar():
    instrutor = regras.criar(request.get_json(silent=True))
    return jsonify(instrutor.to_dict()), 201


@bp.put("/instrutores/<int:instrutor_id>")
def atualizar(instrutor_id):
    instrutor = regras.atualizar(instrutor_id, request.get_json(silent=True))
    return jsonify(instrutor.to_dict())


@bp.delete("/instrutores/<int:instrutor_id>")
def remover(instrutor_id):
    regras.remover(instrutor_id)
    return jsonify({"mensagem": f"Instrutor {instrutor_id} removido."})
