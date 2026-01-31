from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate # <--- IMPORTAÇÃO NOVA
from config import Config
from models import db, Igreja, Usuario
import os
from utils.saas import configurar_isolamento_saas

app = Flask(__name__)
app.config.from_object(Config)

# Inicializações
db.init_app(app)
migrate = Migrate(app, db) # <--- INICIALIZAÇÃO DA MIGRAÇÃO

# Ativa o "Guarda-Costas" SaaS
with app.app_context():
    configurar_isolamento_saas(db.session)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# --- REGISTRO DOS BLUEPRINTS ---
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.membros import membros_bp
from routes.financeiro import financeiro_bp
from routes.usuarios import usuarios_bp
from routes.configuracoes import config_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(membros_bp)
app.register_blueprint(financeiro_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(config_bp)

# --- INICIALIZAÇÃO DE BANCO E SEED ---
# ATENÇÃO: Removemos o db.create_all() automático!
# O banco agora é gerenciado pelos comandos 'flask db ...'
# Mantemos apenas a criação de pastas e o Seed (que só roda se o banco existir)

def criar_seed():
    with app.app_context():
        # Verifica se as tabelas existem antes de tentar inserir
        # (O try/except evita erro se rodar o app antes da primeira migração)
        try:
            if not Igreja.query.first():
                print("--- SEED: Criando dados iniciais... ---")
                igreja = Igreja(
                    nome="IGREJA ASSEMBLEIA DE DEUS, JESUS CRISTO É O CENTRO",
                    cnpj="59.767.708/0001-15",
                    endereco="Av. Vitória Régia, 3170 - Birigui/SP",
                    cidade_uf="Birigui - SP",
                    responsavel="LEANDRO APARECIDO DE SOUZA",
                    cargo_responsavel="Pastor Presidente"
                )
                db.session.add(igreja)
                db.session.commit()
                
                admin = Usuario(nome="Administrador", email="admin@ekklesia.com", role="admin", igreja_id=igreja.id)
                admin.set_senha("admin123")
                db.session.add(admin)
                db.session.commit()
                print("--- SEED CONCLUÍDO ---")
        except Exception:
            pass # Banco ainda não migrado, ignora o seed por enquanto

# Cria pastas necessárias
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(Config.BASE_DIR, 'static', 'logos'), exist_ok=True)

# Executa seed ao iniciar (opcional, melhor seria via comando CLI, mas mantém simples por enquanto)
criar_seed()

if __name__ == '__main__':
    app.run(debug=True)