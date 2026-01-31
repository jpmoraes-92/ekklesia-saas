from flask import Blueprint, render_template
from flask_login import login_required
from models import Membro

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # SEGURANÇA SAAS: 
    # Não precisamos mais filtrar por igreja_id=current_user.igreja_id.
    # O "Guarda-Costas" (utils/saas.py) injeta esse filtro automaticamente.
    
    # Contagem total de membros ativos
    total_membros = Membro.query.filter_by(ativo=True, deleted_at=None).count()
    
    # Últimos 5 membros cadastrados
    ultimos = Membro.query.filter_by(deleted_at=None).order_by(Membro.id.desc()).limit(5).all()
    
    return render_template('dashboard.html', total=total_membros, recentes=ultimos)