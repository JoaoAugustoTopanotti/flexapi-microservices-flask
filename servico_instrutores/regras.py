import logging

from models import db, Instrutor

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
    if not dados.get("especialidade"):
        raise ErroRegra("O campo 'especialidade' é obrigatório.")
    return dados["nome"], dados["especialidade"], dados.get("cref")


def listar():
    return [i.to_dict() for i in Instrutor.query.all()]


def buscar(instrutor_id):
    instrutor = db.session.get(Instrutor, instrutor_id)
    if not instrutor:
        raise ErroRegra(f"Instrutor {instrutor_id} não encontrado.", 404)
    return instrutor


def criar(dados):
    nome, especialidade, cref = validar_dados(dados)
    instrutor = Instrutor(nome=nome, especialidade=especialidade, cref=cref)
    db.session.add(instrutor)
    db.session.commit()
    log.info("Instrutor criado: id=%s nome=%s", instrutor.id, instrutor.nome)
    return instrutor


def atualizar(instrutor_id, dados):
    instrutor = buscar(instrutor_id)
    instrutor.nome, instrutor.especialidade, instrutor.cref = validar_dados(dados)
    db.session.commit()
    log.info("Instrutor atualizado: id=%s", instrutor.id)
    return instrutor


def remover(instrutor_id):
    instrutor = buscar(instrutor_id)
    db.session.delete(instrutor)
    db.session.commit()
    log.info("Instrutor removido: id=%s", instrutor_id)


def popular_dados_iniciais():
    if Instrutor.query.count() == 0:
        db.session.add_all([
            Instrutor(nome="Carlos Souza", especialidade="Musculação", cref="012345-G/SC"),
            Instrutor(nome="Fernanda Lima", especialidade="Funcional", cref="067890-G/SC"),
        ])
        db.session.commit()
        log.info("Dados iniciais de instrutores criados.")
