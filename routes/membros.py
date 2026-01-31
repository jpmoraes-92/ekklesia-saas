from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from models import db, Membro, LogAuditoria
from services.pdf_service import PDFService
from services.card_service import CardService
from config import Config
from datetime import datetime
import os
from PIL import Image
from sqlalchemy.exc import IntegrityError
from markupsafe import Markup

membros_bp = Blueprint('membros', __name__, url_prefix='/membros')

# Função auxiliar de log (poderia ir para um utils.py no futuro)
def registrar_log(acao, entidade, id_ref, detalhes):
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        novo_log = LogAuditoria(acao=acao, entidade=entidade, entidade_id=id_ref, detalhes=detalhes, usuario_id=user_id)
        db.session.add(novo_log)
    except Exception:
        pass

@membros_bp.route('/')
@login_required
def lista():
    membros = Membro.query.filter_by(igreja_id=current_user.igreja_id, deleted_at=None).all()
    return render_template('membros/lista.html', membros=membros)

@membros_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    if request.method == 'POST':
        try:
            novo = Membro(
                nome=request.form['nome'],
                sexo=request.form['sexo_logica'],
                estado_civil=request.form['estado_civil'],
                rg=request.form['rg'],
                cpf=request.form['cpf'],
                endereco=request.form['endereco'],
                data_nascimento=datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d'),
                cargo=request.form.get('cargo', 'Membro'),
                ativo=True,
                igreja_id=current_user.igreja_id
            )
            db.session.add(novo)
            db.session.flush()
            registrar_log("CREATE", "Membro", novo.id, f"Cadastro: {novo.nome}")

            if 'foto' in request.files:
                arquivo = request.files['foto']
                if arquivo.filename != '':
                    img = Image.open(arquivo)
                    caminho = os.path.join(Config.UPLOAD_FOLDER, f"membro_{novo.id}.png")
                    img.convert("RGBA").save(caminho, "PNG")

            db.session.commit()
            flash('Membro cadastrado!')
            return redirect(url_for('membros.lista'))
            
        except IntegrityError:
            db.session.rollback()
            existente = Membro.query.filter_by(cpf=request.form['cpf'], igreja_id=current_user.igreja_id).first()
            if existente and existente.deleted_at:
                # Note o uso de 'membros.reativar' no url_for
                msg = Markup(f"CPF de <strong>{existente.nome}</strong> (Arquivado). <form action='{url_for('membros.reativar', id=existente.id)}' method='POST' class='d-inline'><button class='btn btn-sm btn-success'>Reativar?</button></form>")
                flash(msg)
            else:
                flash('CPF já existente.')
            return redirect(url_for('membros.novo'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}')
            return redirect(url_for('membros.novo'))
    
    return render_template('membros/formulario.html', membro=None, data_hoje=datetime.today().strftime('%Y-%m-%d'))

@membros_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    membro = Membro.query.filter_by(id=id, igreja_id=current_user.igreja_id, deleted_at=None).first_or_404()
    
    if request.method == 'POST':
        try:
            membro.nome = request.form['nome']
            membro.sexo = request.form['sexo_logica']
            membro.estado_civil = request.form['estado_civil']
            membro.rg = request.form['rg']
            membro.cpf = request.form['cpf']
            membro.endereco = request.form['endereco']
            membro.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d')
            membro.cargo = request.form.get('cargo')
            membro.ativo = 'ativo' in request.form 
            
            if 'foto' in request.files:
                arquivo = request.files['foto']
                if arquivo.filename != '':
                    img = Image.open(arquivo)
                    caminho = os.path.join(Config.UPLOAD_FOLDER, f"membro_{membro.id}.png")
                    img.convert("RGBA").save(caminho, "PNG")

            registrar_log("UPDATE", "Membro", membro.id, "Edição de dados")
            db.session.commit()
            flash('Atualizado com sucesso!')
            return redirect(url_for('membros.lista'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro: {e}')
            
    return render_template('membros/formulario.html', membro=membro)

@membros_bp.route('/arquivar/<int:id>', methods=['POST'])
@login_required
def arquivar(id):
    membro = Membro.query.filter_by(id=id, igreja_id=current_user.igreja_id).first_or_404()
    membro.deleted_at = datetime.utcnow()
    membro.ativo = False
    registrar_log("ARCHIVE", "Membro", membro.id, "Arquivado")
    db.session.commit()
    flash('Membro arquivado.')
    return redirect(url_for('membros.lista'))

@membros_bp.route('/reativar/<int:id>', methods=['POST'])
@login_required
def reativar(id):
    membro = Membro.query.filter_by(id=id, igreja_id=current_user.igreja_id).first_or_404()
    membro.deleted_at = None
    membro.ativo = True
    registrar_log("REACTIVATE", "Membro", membro.id, "Reativado")
    db.session.commit()
    flash(f'{membro.nome} reativado.')
    return redirect(url_for('membros.editar', id=membro.id))

@membros_bp.route('/<int:id>/declaracao')
@login_required
def declaracao(id):
    membro = Membro.query.filter_by(id=id, igreja_id=current_user.igreja_id, deleted_at=None).first_or_404()
    dados = {
        'nome': membro.nome, 'rg': membro.rg, 'cpf': membro.cpf,
        'estado_civil': membro.estado_civil, 'endereco': membro.endereco,
        'sexo': membro.sexo, 'data_declaracao': datetime.today().strftime('%Y-%m-%d')
    }
    pdf_bytes = PDFService().gerar_declaracao(dados)
    response = make_response(bytes(pdf_bytes))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=Declaracao.pdf'
    return response

@membros_bp.route('/<int:id>/carteirinha')
@login_required
def carteirinha(id):
    membro = Membro.query.filter_by(id=id, igreja_id=current_user.igreja_id, deleted_at=None).first_or_404()
    img_bytes = CardService().gerar_frente(membro)
    response = make_response(img_bytes.getvalue())
    response.headers['Content-Type'] = 'image/png'
    response.headers['Content-Disposition'] = 'inline; filename=Carteirinha.png'
    return response