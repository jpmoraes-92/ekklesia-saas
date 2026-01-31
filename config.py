import os
# Tenta importar dotenv (caso não tenha instalado, não quebra, mas é recomendado)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # SEGURANÇA: A chave agora vem do ambiente (.env)
    # Se não houver .env (produção), o sistema pode falhar se não configurado, o que é seguro.
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave-padrao-insegura-apenas-para-dev')
    
    # Banco de Dados
    # Prepara para PostgreSQL (Render/Railway) mas mantém SQLite local
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'ekklesia.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # DADOS DA IGREJA (Fallback para PDFService antigo)
    IGREJA_NOME = "IGREJA ASSEMBLEIA DE DEUS, JESUS CRISTO É O CENTRO"
    IGREJA_CNPJ = "59.767.708/0001-15"
    IGREJA_ENDERECO = "Avenida Vitória Régia, 3170 - Residencial Quinta da Mata"
    IGREJA_CIDADE_UF = "Birigui - SP"
    IGREJA_CEP = "16.202-538"
    ASSINANTE_NOME = "LEANDRO APARECIDO DE SOUZA"
    ASSINANTE_CARGO = "Pastor Presidente"
    LOGO_PATH = os.path.join(BASE_DIR, 'static', 'img', 'logo_igreja.jpg')