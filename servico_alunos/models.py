from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

SITUACOES = ("pendente", "em dia")


class Aluno(db.Model):
    __tablename__ = "alunos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    # Apenas os ids dos outros serviços (sem ForeignKey entre bancos)
    plano_id = db.Column(db.Integer, nullable=False)
    instrutor_id = db.Column(db.Integer, nullable=True)
    ativo = db.Column(db.Boolean, nullable=False, default=True)
    situacao_pagamento = db.Column(db.String(20), nullable=False, default="pendente")
    ultimo_pagamento_id = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "plano_id": self.plano_id,
            "instrutor_id": self.instrutor_id,
            "ativo": self.ativo,
            "situacao_pagamento": self.situacao_pagamento,
            "ultimo_pagamento_id": self.ultimo_pagamento_id,
        }
