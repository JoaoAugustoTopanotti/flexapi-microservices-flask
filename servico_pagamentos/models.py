from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Pagamento(db.Model):
    __tablename__ = "pagamentos"

    id = db.Column(db.Integer, primary_key=True)
    # Apenas o id do aluno (sem ForeignKey entre bancos)
    aluno_id = db.Column(db.Integer, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    referencia = db.Column(db.String(7), nullable=False)  # ex.: "2026-11"
    forma = db.Column(db.String(20), nullable=False, default="pix")
    data = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "aluno_id": self.aluno_id,
            "valor": self.valor,
            "referencia": self.referencia,
            "forma": self.forma,
            "data": self.data.isoformat(timespec="seconds"),
        }
