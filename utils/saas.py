from sqlalchemy import event
from sqlalchemy.orm import Session, with_loader_criteria
from flask_login import current_user
from models import Membro, Lancamento, Usuario

def configurar_isolamento_saas(db_session):
    """
    Ativa o 'Guarda-Costas' do Banco de Dados.
    Intercepta TODAS as consultas SQL e adiciona o filtro da igreja automaticamente.
    """
    
    @event.listens_for(Session, 'do_orm_execute')
    def interceptar_consulta(execute_state):
        
        # 1. Só age se for uma consulta de LEITURA (SELECT)
        if not execute_state.is_select:
            return

        # 2. Só age se tiver alguém logado
        if not current_user or not current_user.is_authenticated:
            return
            
        # 3. TRUQUE ANTI-RECURSÃO (Safety Fix):
        # Precisamos capturar o ID da igreja AGORA, numa variável local.
        # Se tentarmos ler 'current_user.igreja_id' dentro do lambda do SQLAlchemy,
        # isso pode disparar uma nova consulta e criar um Loop Infinito.
        try:
            tenant_id = current_user.igreja_id
        except:
            # Se der erro ao ler o ID (ex: usuário ainda carregando), não aplica filtro
            return

        # 4. APLICA O FILTRO AUTOMÁTICO (Simulação de RLS)
        execute_state.statement = execute_state.statement.options(
            # Protege a tabela Membros
            with_loader_criteria(
                Membro, 
                lambda cls: cls.igreja_id == tenant_id,
                include_aliases=True
            ),
            # Protege a tabela Financeiro
            with_loader_criteria(
                Lancamento, 
                lambda cls: cls.igreja_id == tenant_id,
                include_aliases=True
            )
            
        )