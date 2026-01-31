from app import app
from models import db, Membro, Igreja

with app.app_context():
    print("-" * 30)
    print("AUDITORIA DO BANCO DE DADOS (SEM FILTRO SAAS)")
    print("-" * 30)
    
    # Vamos usar SQL puro para ignorar o filtro do SQLAlchemy por um momento
    # ou consultar a tabela Igreja para ver quem existe
    
    igrejas = Igreja.query.all()
    print(f"Total de Igrejas: {len(igrejas)}")
    for i in igrejas:
        print(f"ID: {i.id} | Nome: {i.nome}")

    print("\n--- MEMBROS NO BANCO (TOTAL FÍSICO) ---")
    # Aqui usamos uma sessão pura para ver se os dados existem fisicamente
    # Nota: O filtro SAAS atua no ORM. Se consultarmos via SQL bruto, vemos tudo.
    
    con = db.engine.connect()
    result = con.execute(db.text("SELECT nome, igreja_id FROM membro"))
    
    for row in result:
        print(f"Membro: {row[0]} | Pertence à Igreja ID: {row[1]}")
        
    print("-" * 30)