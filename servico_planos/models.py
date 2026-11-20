from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Plano(db.Model):
    __tablename__ = "planos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(60), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    duracao_meses = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "valor": self.valor,
            "duracao_meses": self.duracao_meses,
        }
