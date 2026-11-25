import logging

import instrutores_helper
import planos_helper
from models import db, Aluno, SITUACOES

log = logging.getLogger(__name__)


class ErroRegra(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def validar_dados(dados):
    if not dados:
        raise ErroRegra("Envie um JSON no corpo da requisição.")
    for campo in ("nome", "email", "plano_id"):
        if not dados.get(campo):
            raise ErroRegra(f"O campo '{campo}' é obrigatório.")
    return dados


def validar_plano(plano_id):
    """confere se plano existe no serviço de planos."""
    try:
        plano = planos_helper.buscar_plano(plano_id)
    except planos_helper.ServicoIndisponivel as e:
        raise ErroRegra(str(e), 503)
    if plano is None:
        raise ErroRegra(f"Plano {plano_id} não existe no serviço de planos.", 422)


def listar():
    return [a.to_dict() for a in Aluno.query.all()]


def buscar(aluno_id):
    aluno = db.session.get(Aluno, aluno_id)
    if not aluno:
        raise ErroRegra(f"Aluno {aluno_id} não encontrado.", 404)
    return aluno


def buscar_detalhado(aluno_id):
    """busca aluno com plano e instrutor anexados. serviço fora do ar vira erro no campo, não quebra request."""
    aluno = buscar(aluno_id)
    resultado = aluno.to_dict()

    try:
        resultado["plano"] = planos_helper.buscar_plano(aluno.plano_id) or {
            "erro": f"Plano {aluno.plano_id} não encontrado."
        }
    except planos_helper.ServicoIndisponivel as e:
        resultado["plano"] = {"erro": str(e)}

    if aluno.instrutor_id:
        try:
            resultado["instrutor"] = instrutores_helper.buscar_instrutor(aluno.instrutor_id) or {
                "erro": f"Instrutor {aluno.instrutor_id} não encontrado."
            }
        except instrutores_helper.ServicoIndisponivel as e:
            resultado["instrutor"] = {"erro": str(e)}

    return resultado


def criar(dados):
    validar_dados(dados)
    validar_plano(dados["plano_id"])
    aluno = Aluno(
        nome=dados["nome"],
        email=dados["email"],
        plano_id=dados["plano_id"],
        instrutor_id=dados.get("instrutor_id"),
        ativo=dados.get("ativo", True),
    )
    db.session.add(aluno)
    db.session.commit()
    log.info("Aluno criado: id=%s nome=%s", aluno.id, aluno.nome)
    return aluno


def atualizar(aluno_id, dados):
    aluno = buscar(aluno_id)
    validar_dados(dados)
    if dados["plano_id"] != aluno.plano_id:
        validar_plano(dados["plano_id"])
    aluno.nome = dados["nome"]
    aluno.email = dados["email"]
    aluno.plano_id = dados["plano_id"]
    aluno.instrutor_id = dados.get("instrutor_id")
    aluno.ativo = dados.get("ativo", aluno.ativo)
    db.session.commit()
    log.info("Aluno atualizado: id=%s", aluno.id)
    return aluno


def alterar_situacao(aluno_id, dados):
    """chamado pelo serviço pagamentos pra marcar aluno 'em dia'."""
    aluno = buscar(aluno_id)
    situacao = (dados or {}).get("situacao_pagamento")
    if situacao not in SITUACOES:
        raise ErroRegra(f"'situacao_pagamento' deve ser um destes: {', '.join(SITUACOES)}.")
    aluno.situacao_pagamento = situacao
    if "pagamento_id" in dados:
        aluno.ultimo_pagamento_id = dados["pagamento_id"]
    db.session.commit()
    log.info("Situação do aluno %s alterada para '%s'", aluno.id, situacao)
    return aluno


def remover(aluno_id):
    aluno = buscar(aluno_id)
    db.session.delete(aluno)
    db.session.commit()
    log.info("Aluno removido: id=%s", aluno_id)


def popular_dados_iniciais():
    if Aluno.query.count() == 0:
        db.session.add_all([
            Aluno(nome="Ana Pereira", email="ana@email.com", plano_id=1, instrutor_id=1),
            Aluno(nome="Bruno Costa", email="bruno@email.com", plano_id=3, instrutor_id=2),
            Aluno(nome="Camila Rocha", email="camila@email.com", plano_id=2, ativo=False),
        ])
        db.session.commit()
        log.info("Dados iniciais de alunos criados.")
