import logging

from models import db, Plano

log = logging.getLogger(__name__)


class ErroRegra(Exception):
    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def validar_dados(dados):
    if not dados:
        raise ErroRegra("Envie um JSON no corpo da requisição.")
    if not dados.get("nome"):
        raise ErroRegra("O campo 'nome' é obrigatório.")
    try:
        valor = float(dados.get("valor"))
    except (TypeError, ValueError):
        raise ErroRegra("O campo 'valor' é obrigatório e deve ser numérico.")
    if valor <= 0:
        raise ErroRegra("O 'valor' deve ser maior que zero.")
    duracao = int(dados.get("duracao_meses", 1))
    if duracao < 1:
        raise ErroRegra("A 'duracao_meses' deve ser pelo menos 1.")
    return dados["nome"], valor, duracao


def listar():
    return [p.to_dict() for p in Plano.query.all()]


def buscar(plano_id):
    plano = db.session.get(Plano, plano_id)
    if not plano:
        raise ErroRegra(f"Plano {plano_id} não encontrado.", 404)
    return plano


def criar(dados):
    nome, valor, duracao = validar_dados(dados)
    plano = Plano(nome=nome, valor=valor, duracao_meses=duracao)
    db.session.add(plano)
    db.session.commit()
    log.info("Plano criado: id=%s nome=%s", plano.id, plano.nome)
    return plano


def atualizar(plano_id, dados):
    plano = buscar(plano_id)
    nome, valor, duracao = validar_dados(dados)
    plano.nome, plano.valor, plano.duracao_meses = nome, valor, duracao
    db.session.commit()
    log.info("Plano atualizado: id=%s", plano.id)
    return plano


def remover(plano_id):
    plano = buscar(plano_id)
    db.session.delete(plano)
    db.session.commit()
    log.info("Plano removido: id=%s", plano_id)


def popular_dados_iniciais():
    if Plano.query.count() == 0:
        db.session.add_all([
            Plano(nome="Mensal", valor=99.90, duracao_meses=1),
            Plano(nome="Trimestral", valor=269.90, duracao_meses=3),
            Plano(nome="Anual", valor=899.90, duracao_meses=12),
        ])
        db.session.commit()
        log.info("Dados iniciais de planos criados.")
