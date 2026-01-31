from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario, Igreja, LogAuditoria

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and usuario.check_senha(senha):
            login_user(usuario)
            return redirect(url_for('dashboard.index'))
        else:
            flash('E-mail ou senha inválidos.')
            
    return render_template('login.html')

@auth_bp.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        try:
            # 1. Captura dados do formulário
            nome_igreja = request.form['nome_igreja']
            nome_admin = request.form['nome_admin']
            email = request.form['email']
            senha = request.form['senha']
            
            # 2. Verifica se e-mail já existe (Globalmente)
            if Usuario.query.filter_by(email=email).first():
                flash('Este e-mail já está cadastrado. Tente fazer login.')
                return redirect(url_for('auth.registrar'))
            
            # 3. Criação Transacional (Tudo ou Nada)
            # Passo A: Criar a Organização (Igreja)
            nova_igreja = Igreja(
                nome=nome_igreja,
                # Campos opcionais ficam vazios para preencher depois em Configurações
                endereco="Endereço não configurado",
                cidade_uf="Cidade - UF"
            )
            db.session.add(nova_igreja)
            db.session.flush() # Gera o ID da igreja sem fechar a transação
            
            # Passo B: Criar o Dono da Conta (Admin)
            novo_admin = Usuario(
                nome=nome_admin,
                email=email,
                role='admin', # Importante: Ele é Admin da própria igreja
                igreja_id=nova_igreja.id
            )
            novo_admin.set_senha(senha)
            db.session.add(novo_admin)
            
            # Passo C: Efetivar tudo
            db.session.commit()
            
            # 4. Auditoria Inicial
            # Como o usuário ainda não está logado na sessão, inserimos o ID manualmente ou deixamos null
            # Mas vamos logar ele agora:
            login_user(novo_admin)
            
            # Registrar Log de Boas Vindas
            db.session.add(LogAuditoria(
                acao="SIGNUP", entidade="Igreja", entidade_id=nova_igreja.id, 
                detalhes=f"Nova organização criada: {nova_igreja.nome}", usuario_id=novo_admin.id
            ))
            db.session.commit()
            
            flash(f'Bem-vindo ao EkklesiaApp! Configure os dados da sua igreja.')
            # Redireciona direto para configurações para ele terminar o cadastro
            return redirect(url_for('configuracoes.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar conta: {str(e)}')
            
    return render_template('registrar.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))