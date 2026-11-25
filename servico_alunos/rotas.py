from flask import Blueprint, jsonify, request

import regras
from regras import ErroRegra

bp = Blueprint("alunos", __name__)


@bp.errorhandler(ErroRegra)
def tratar_erro(e):
    return jsonify({"erro": e.mensagem}), e.status


@bp.get("/")
def status():
    return jsonify({"servico": "alunos", "status": "ok"})


@bp.get("/alunos")
def listar():
    return jsonify(regras.listar())


@bp.get("/alunos/<int:aluno_id>")
def buscar(aluno_id):
    return jsonify(regras.buscar_detalhado(aluno_id))


@bp.post("/alunos")
def criar():
    aluno = regras.criar(request.get_json(silent=True))
    return jsonify(aluno.to_dict()), 201


@bp.put("/alunos/<int:aluno_id>")
def atualizar(aluno_id):
    aluno = regras.atualizar(aluno_id, request.get_json(silent=True))
    return jsonify(aluno.to_dict())


@bp.patch("/alunos/<int:aluno_id>/situacao")
def alterar_situacao(aluno_id):
    aluno = regras.alterar_situacao(aluno_id, request.get_json(silent=True))
    return jsonify(aluno.to_dict())


@bp.delete("/alunos/<int:aluno_id>")
def remover(aluno_id):
    regras.remover(aluno_id)
    return jsonify({"mensagem": f"Aluno {aluno_id} removido."})
