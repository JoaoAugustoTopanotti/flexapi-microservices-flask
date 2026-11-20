from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Instrutor(db.Model):
    __tablename__ = "instrutores"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(60), nullable=False)
    cref = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "especialidade": self.especialidade,
            "cref": self.cref,
        }
