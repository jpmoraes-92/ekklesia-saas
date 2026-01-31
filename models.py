from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Igreja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(20))
    endereco = db.Column(db.String(200))
    cidade_uf = db.Column(db.String(50))
    responsavel = db.Column(db.String(100))
    cargo_responsavel = db.Column(db.String(50))
    membros = db.relationship('Membro', backref='igreja', lazy=True)
    usuarios = db.relationship('Usuario', backref='igreja', lazy=True)

class Usuario(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128))
    
    # Campo de Nível de Acesso (admin, secretaria, financeiro)
    role = db.Column(db.String(20), default='secretaria', nullable=False)
    
    igreja_id = db.Column(db.Integer, db.ForeignKey('igreja.id'), nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)
    
    # Helper para verificar se é admin no template
    @property
    def is_admin(self):
        return self.role == 'admin'

class Membro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    sexo = db.Column(db.String(1))
    estado_civil = db.Column(db.String(20))
    rg = db.Column(db.String(20))
    cpf = db.Column(db.String(14), unique=True)
    endereco = db.Column(db.String(200))
    data_nascimento = db.Column(db.Date)
    data_batismo = db.Column(db.Date, nullable=True)
    cargo = db.Column(db.String(50), default='Membro')
    ativo = db.Column(db.Boolean, default=True)
    telefone = db.Column(db.String(20))
    
    deleted_at = db.Column(db.DateTime, nullable=True)
    
    igreja_id = db.Column(db.Integer, db.ForeignKey('igreja.id'), nullable=False)

class LogAuditoria(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    acao = db.Column(db.String(50))
    entidade = db.Column(db.String(50))
    entidade_id = db.Column(db.Integer)
    detalhes = db.Column(db.Text)
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=True)
    usuario = db.relationship('Usuario')

class Lancamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    tipo = db.Column(db.String(10), nullable=False) # 'entrada' ou 'saida'
    categoria = db.Column(db.String(50), nullable=False) # Ex: Dízimo, Oferta, Aluguel, Luz
    descricao = db.Column(db.String(200))
    valor = db.Column(db.Float, nullable=False)
    
    # Relacionamentos
    igreja_id = db.Column(db.Integer, db.ForeignKey('igreja.id'), nullable=False)
    
    # Opcional: Saber quem deu o dízimo (Se for nulo, foi oferta anônima)
    membro_id = db.Column(db.Integer, db.ForeignKey('membro.id'), nullable=True)
    membro = db.relationship('Membro', backref='lancamentos')

    # Auditoria interna
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)