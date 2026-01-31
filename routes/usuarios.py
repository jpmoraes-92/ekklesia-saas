from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Usuario, LogAuditoria
from sqlalchemy.exc import IntegrityError
from functools import wraps

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('🚫 Acesso Negado: Área Restrita.')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def registrar_log(acao, entidade, id_ref, detalhes):
    try:
        user_id = current_user.id
        novo_log = LogAuditoria(acao=acao, entidade=entidade, entidade_id=id_ref, detalhes=detalhes, usuario_id=user_id)
        db.session.add(novo_log)
    except: pass

@usuarios_bp.route('/')
@login_required
@admin_required
def lista():
    usuarios = Usuario.query.filter_by(igreja_id=current_user.igreja_id).all()
    return render_template('usuarios/lista.html', usuarios=usuarios)

@usuarios_bp.route('/novo', methods=['GET', 'POST'])
@login_required
@admin_required
def novo():
    if request.method == 'POST':
        try:
            if Usuario.query.filter_by(email=request.form['email']).first():
                flash('E-mail já cadastrado.')
                return redirect(url_for('usuarios.novo'))

            novo = Usuario(
                nome=request.form['nome'],
                email=request.form['email'],
                role=request.form['role'],
                igreja_id=current_user.igreja_id
            )
            novo.set_senha(request.form['senha'])
            
            db.session.add(novo)
            db.session.flush()
            registrar_log("CREATE_USER", "Usuario", novo.id, f"Criou: {novo.email}")
            db.session.commit()
            
            flash('Usuário criado!')
            return redirect(url_for('usuarios.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}')
            
    return render_template('usuarios/formulario.html')