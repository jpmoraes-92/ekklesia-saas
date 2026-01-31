from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Lancamento, Membro, LogAuditoria
from datetime import datetime

financeiro_bp = Blueprint('financeiro', __name__, url_prefix='/financeiro')

@financeiro_bp.route('/')
@login_required
def index():
    # Filtra lançamentos da igreja do usuário
    lancamentos = Lancamento.query.filter_by(igreja_id=current_user.igreja_id).order_by(Lancamento.data.desc()).all()
    
    # Cálculo simples de Saldo (No futuro faremos via SQL para performance)
    total_entradas = sum(l.valor for l in lancamentos if l.tipo == 'entrada')
    total_saidas = sum(l.valor for l in lancamentos if l.tipo == 'saida')
    saldo = total_entradas - total_saidas
    
    return render_template('financeiro/index.html', 
                           lancamentos=lancamentos, 
                           entradas=total_entradas, 
                           saidas=total_saidas, 
                           saldo=saldo)

@financeiro_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            valor = float(request.form['valor'].replace(',', '.')) # Trata R$ brasileiro
            
            novo_lancamento = Lancamento(
                data=datetime.strptime(request.form['data'], '%Y-%m-%d'),
                tipo=request.form['tipo'],
                categoria=request.form['categoria'],
                descricao=request.form['descricao'],
                valor=valor,
                igreja_id=current_user.igreja_id,
                membro_id=request.form.get('membro_id') or None # Se vazio, vira None
            )
            
            db.session.add(novo_lancamento)
            db.session.commit()
            
            # Log de Auditoria
            user_id = current_user.id
            db.session.add(LogAuditoria(
                acao="CREATE_FIN", 
                entidade="Lancamento", 
                entidade_id=novo_lancamento.id, 
                detalhes=f"{novo_lancamento.tipo} de R$ {novo_lancamento.valor}",
                usuario_id=user_id
            ))
            db.session.commit()
            
            flash('Lançamento registrado com sucesso!')
            return redirect(url_for('financeiro.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}')
            
    # Carrega membros para o select de Dízimo
    membros = Membro.query.filter_by(igreja_id=current_user.igreja_id, deleted_at=None).all()
    return render_template('financeiro/formulario.html', membros=membros, hoje=datetime.today().strftime('%Y-%m-%d'))