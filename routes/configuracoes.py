from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Igreja, LogAuditoria
from config import Config
import os
from PIL import Image
from functools import wraps

config_bp = Blueprint('configuracoes', __name__, url_prefix='/configuracoes')

# Decorator para garantir que só Admin mexa aqui
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('🚫 Acesso restrito a Administradores.')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@config_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    # Pega a igreja do usuário logado
    igreja = Igreja.query.get(current_user.igreja_id)
    
    if request.method == 'POST':
        try:
            # Atualiza dados cadastrais
            igreja.nome = request.form['nome']
            igreja.cnpj = request.form['cnpj']
            igreja.responsavel = request.form['responsavel']
            igreja.cargo_responsavel = request.form['cargo_responsavel']
            igreja.endereco = request.form['endereco']
            igreja.cidade_uf = request.form['cidade_uf']
            
            # Processamento de Upload da Logo
            if 'logo' in request.files:
                arquivo = request.files['logo']
                if arquivo.filename != '':
                    # Salva como logo_{id}.png para garantir unicidade
                    img = Image.open(arquivo)
                    nome_arquivo = f"logo_{igreja.id}.png"
                    
                    # Cria pasta de logos se não existir
                    pasta_logos = os.path.join(Config.BASE_DIR, 'static', 'logos')
                    os.makedirs(pasta_logos, exist_ok=True)
                    
                    caminho_salvar = os.path.join(pasta_logos, nome_arquivo)
                    img.convert("RGBA").save(caminho_salvar, "PNG")
                    
                    # Auditoria
                    db.session.add(LogAuditoria(
                        acao="UPDATE_LOGO", entidade="Igreja", entidade_id=igreja.id, 
                        detalhes="Logo atualizada", usuario_id=current_user.id
                    ))

            db.session.commit()
            
            # Auditoria de dados
            db.session.add(LogAuditoria(
                acao="UPDATE_CONFIG", entidade="Igreja", entidade_id=igreja.id, 
                detalhes="Dados institucionais atualizados", usuario_id=current_user.id
            ))
            db.session.commit()
            
            flash('Configurações salvas com sucesso!')
            return redirect(url_for('configuracoes.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar: {e}')
            
    return render_template('configuracoes/formulario.html', igreja=igreja)