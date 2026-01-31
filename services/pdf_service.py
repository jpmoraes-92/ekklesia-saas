from fpdf import FPDF
from config import Config
import os
from datetime import datetime
from flask_login import current_user

class PDFService(FPDF):
    def header(self):
        # 1. Pega os dados da igreja do usuário logado
        igreja = current_user.igreja
        
        # 2. Lógica Inteligente da Logo
        # Tenta pegar a logo personalizada (ex: static/logos/logo_1.png)
        nome_logo_custom = f"logo_{igreja.id}.png"
        caminho_logo_custom = os.path.join(Config.BASE_DIR, 'static', 'logos', nome_logo_custom)
        
        # Define qual logo usar
        logo_para_usar = None
        if os.path.exists(caminho_logo_custom):
            logo_para_usar = caminho_logo_custom
        elif os.path.exists(Config.LOGO_PATH): # Fallback para logo padrão
            logo_para_usar = Config.LOGO_PATH
            
        # Desenha a logo se encontrou alguma
        if logo_para_usar:
            # Centraliza a logo (A4=210mm. Margem=25mm. Logo=30mm)
            self.image(logo_para_usar, x=90, y=10, w=30)
        
        self.ln(35) # Espaço vertical após a logo

        # 3. Cabeçalho com dados do Banco
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, self._tratar_texto(igreja.nome), align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "", 10)
        self.cell(0, 5, f"CNPJ: {igreja.cnpj}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10) 

    def footer(self):
        # Rodapé com endereço do Banco
        igreja = current_user.igreja
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        texto_rodape = f"{igreja.endereco}, {igreja.cidade_uf}"
        self.cell(0, 10, self._tratar_texto(texto_rodape), align="C")

    def _tratar_texto(self, texto):
        """Corrige acentuação para fontes padrão"""
        if not texto: return ""
        try:
            return texto.encode('latin-1', 'replace').decode('latin-1')
        except:
            return texto

    def gerar_declaracao(self, dados_membro):
        igreja = current_user.igreja
        
        self.add_page()
        self.set_margins(25, 25, 25) 
        
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, self._tratar_texto("DECLARAÇÃO DE MEMBRESIA"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(15)

        self.set_font("Helvetica", "", 12)
        
        # Lógica de Gênero
        if dados_membro.get('sexo') == 'M':
            tratamento = "o Sr."
            nacionalidade = "brasileiro"
            portador = "portador"
            referido = "o referido membro"
        else:
            tratamento = "a Sra."
            nacionalidade = "brasileira"
            portador = "portadora"
            referido = "a referida membro"

        # Texto do Corpo
        texto_corpo = (
            f"Declaramos, para os devidos fins de direito e a quem possa interessar, "
            f"especialmente para comprovação junto a instituições de ensino, que {tratamento} "
            f"{dados_membro['nome'].upper()}, {nacionalidade}, {dados_membro['estado_civil']}, "
            f"{portador} do RG nº {dados_membro['rg']}, CPF nº {dados_membro['cpf']}, "
            f"residente e domiciliado(a) na {dados_membro['endereco']}, nesta cidade, "
            f"é membro ativo(a) e em regular comunhão com esta instituição religiosa.\n\n"
            f"Atestamos que {referido} frequenta as atividades desta organização religiosa, "
            f"cuja natureza jurídica é de Organização Religiosa (322-0), devidamente inscrita "
            f"no CNPJ sob o nº {igreja.cnpj}.\n\n"
            f"Por ser expressão da verdade, firmamos a presente declaração."
        )

        self.multi_cell(0, 8, self._tratar_texto(texto_corpo), align="J")
        
        self.ln(20)

        # Data e Local
        data_obj = datetime.strptime(dados_membro['data_declaracao'], '%Y-%m-%d')
        data_formatada = data_obj.strftime('%d/%m/%Y')
        
        texto_data = f"{igreja.cidade_uf}, {data_formatada}."
        self.cell(0, 10, self._tratar_texto(texto_data), align="R", new_x="LMARGIN", new_y="NEXT")

        self.ln(30) 

        # Assinatura do Banco
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 6, self._tratar_texto(igreja.responsavel), align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, self._tratar_texto(igreja.cargo_responsavel), align="C", new_x="LMARGIN", new_y="NEXT")

        return self.output()