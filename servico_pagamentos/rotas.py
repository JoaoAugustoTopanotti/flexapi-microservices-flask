from flask import Blueprint, jsonify, request

import regras
from regras import ErroRegra

bp = Blueprint("pagamentos", __name__)


@bp.errorhandler(ErroRegra)
def tratar_erro(e):
    return jsonify({"erro": e.mensagem}), e.status


@bp.get("/")
def status():
    return jsonify({"servico": "pagamentos", "status": "ok"})


@bp.get("/api/health")
def health():
    return jsonify({"status": "no ar"})


@bp.get("/pagamentos")
def listar():
    return jsonify(regras.listar(request.args.get("aluno_id", type=int)))


@bp.get("/pagamentos/<int:pagamento_id>")
def buscar(pagamento_id):
    return jsonify(regras.buscar(pagamento_id).to_dict())


@bp.post("/pagamentos")
def registrar():
    resultado = regras.registrar(request.get_json(silent=True))
    return jsonify(resultado), 201


@bp.delete("/pagamentos/<int:pagamento_id>")
def remover(pagamento_id):
    regras.remover(pagamento_id)
    return jsonify({"mensagem": f"Pagamento {pagamento_id} removido."})
