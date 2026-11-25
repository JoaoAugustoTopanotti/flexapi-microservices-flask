import logging

import alunos_helper
from models import db, Pagamento

log = logging.getLogger(__name__)

FORMAS = ("pix", "cartao", "dinheiro", "boleto")


class ErroRegra(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def validar_dados(dados):
    if not dados:
        raise ErroRegra("Envie um JSON no corpo da requisição.")
    if not dados.get("aluno_id"):
        raise ErroRegra("O campo 'aluno_id' é obrigatório.")
    if not dados.get("referencia"):
        raise ErroRegra("O campo 'referencia' é obrigatório (ex.: '2026-11').")
    try:
        valor = float(dados.get("valor"))
    except (TypeError, ValueError):
        raise ErroRegra("O campo 'valor' é obrigatório e deve ser numérico.")
    if valor <= 0:
        raise ErroRegra("O 'valor' deve ser maior que zero.")
    forma = dados.get("forma", "pix")
    if forma not in FORMAS:
        raise ErroRegra(f"'forma' deve ser uma destas: {', '.join(FORMAS)}.")
    return valor, forma


def listar(aluno_id=None):
    consulta = Pagamento.query
    if aluno_id:
        consulta = consulta.filter_by(aluno_id=aluno_id)
    return [p.to_dict() for p in consulta.all()]


def buscar(pagamento_id):
    pagamento = db.session.get(Pagamento, pagamento_id)
    if not pagamento:
        raise ErroRegra(f"Pagamento {pagamento_id} não encontrado.", 404)
    return pagamento


def registrar(dados):
    valor, forma = validar_dados(dados)
    aluno_id = dados["aluno_id"]

    try:
        aluno = alunos_helper.buscar_aluno(aluno_id)
    except alunos_helper.ServicoIndisponivel as e:
        raise ErroRegra(str(e), 503)
    if aluno is None:
        raise ErroRegra(f"Aluno {aluno_id} não existe no serviço de alunos.", 404)
    if not aluno.get("ativo"):
        raise ErroRegra(f"O aluno {aluno_id} ({aluno['nome']}) está inativo; pagamento não registrado.", 422)

    pagamento = Pagamento(aluno_id=aluno_id, valor=valor, referencia=dados["referencia"], forma=forma)
    db.session.add(pagamento)
    db.session.commit()
    log.info("Pagamento %s salvo para o aluno %s", pagamento.id, aluno_id)

    try:
        aluno_atualizado = alunos_helper.marcar_em_dia(aluno_id, pagamento.id)
    except alunos_helper.ServicoIndisponivel as e:
        # desfaz pagamento salvo já que marcar 'em dia' falhou (compensação)
        log.error("Compensação: removendo pagamento %s. Motivo: %s", pagamento.id, e)
        db.session.delete(pagamento)
        db.session.commit()
        raise ErroRegra(f"{e} O pagamento foi desfeito (compensação).", 503)

    log.info("Aluno %s agora está 'em dia'", aluno_id)
    return {"pagamento": pagamento.to_dict(), "aluno": aluno_atualizado}


def remover(pagamento_id):
    pagamento = buscar(pagamento_id)
    db.session.delete(pagamento)
    db.session.commit()
    log.info("Pagamento removido: id=%s", pagamento_id)


def popular_dados_iniciais():
    # pagamentos começam vazios, criados via integração na demo
    pass
