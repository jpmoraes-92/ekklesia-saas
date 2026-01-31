from PIL import Image, ImageDraw, ImageFont
import qrcode
from config import Config
import os
from datetime import datetime
import io

class CardService:
    def __init__(self):
        self.WIDTH = 1011
        self.HEIGHT = 638
        
        # --- PALETA DE CORES (PRETO & AMARELO FOGO) ---
        self.COR_FUNDO = (20, 20, 20)          # Preto Suave (Cinza muito escuro)
        self.COR_HEADER_BG = (0, 0, 0)         # Preto Puro (Para fundir com o logo)
        
        # Amarelo/Laranja extraído do Logo (Fogo)
        self.COR_ACCENT = (255, 165, 0)        # Orange
        self.COR_ACCENT_LIGHT = (255, 200, 80) # Amarelo Ouro
        
        self.COR_TEXTO_PRINCIPAL = (255, 255, 255) # Branco
        self.COR_TEXTO_SECUNDARIO = (180, 180, 180) # Cinza Claro
        
        # Fontes
        self.font_Regular = "arial.ttf"
        self.font_Bold = "arialbd.ttf"

    def _carregar_fonte(self, tamanho, bold=False):
        try:
            font_file = self.font_Bold if bold else self.font_Regular
            return ImageFont.truetype(font_file, tamanho)
        except:
            return ImageFont.load_default()

    def _desenhar_texto_ajustavel(self, draw, text, x, y, max_width, initial_size, color, bold=True):
        """
        Reduz o tamanho da fonte até que o texto caiba na largura máxima permitida.
        """
        size = initial_size
        font = self._carregar_fonte(size, bold)
        
        # Loop para reduzir fonte se estourar a largura
        while draw.textlength(text, font=font) > max_width and size > 10:
            size -= 2
            font = self._carregar_fonte(size, bold)
            
        draw.text((x, y), text, font=font, fill=color)
        return size # Retorna o tamanho usado (útil para debug)

    def gerar_frente(self, membro):
        # 1. Base Dark
        img = Image.new('RGB', (self.WIDTH, self.HEIGHT), self.COR_FUNDO)
        draw = ImageDraw.Draw(img)
        
        # --- CABEÇALHO (BANNER PRETO) ---
        altura_header = 200
        draw.rectangle([(0, 0), (self.WIDTH, altura_header)], fill=self.COR_HEADER_BG)
        # Linha Dourada de separação
        draw.rectangle([(0, altura_header), (self.WIDTH, altura_header + 6)], fill=self.COR_ACCENT)

        # --- LOGO DA IGREJA ---
        if os.path.exists(Config.LOGO_PATH):
            try:
                logo = Image.open(Config.LOGO_PATH).convert("RGBA")
                # Redimensiona para caber no header (altura 180px com margem)
                aspect = logo.width / logo.height
                new_h = 160
                new_w = int(new_h * aspect)
                logo = logo.resize((new_w, new_h))
                
                # Cria uma máscara para colar (caso seja PNG transparente)
                # Se for JPG preto, vai fundir com o fundo preto do header
                img.paste(logo, (30, 20), logo if 'A' in logo.getbands() else None)
            except Exception as e:
                print(f"Erro logo: {e}")

        # --- TEXTO DO CABEÇALHO (Alinhado à direita do Logo) ---
        # Parte 1: ASSEMBLEIA DE DEUS
        font_main = self._carregar_fonte(50, bold=True)
        draw.text((380, 50), "ASSEMBLEIA DE DEUS", font=font_main, fill=self.COR_TEXTO_PRINCIPAL)
        
        # Parte 2: JESUS CRISTO É O CENTRO (Dourado)
        font_sub = self._carregar_fonte(28, bold=True)
        draw.text((384, 110), "JESUS CRISTO É O CENTRO", font=font_sub, fill=self.COR_ACCENT)

        # Título da Carteirinha
        draw.text((self.WIDTH - 350, 220), "MEMBRO OFICIAL", font=self._carregar_fonte(30, bold=True), fill=self.COR_ACCENT_LIGHT)

        # --- FOTO DO MEMBRO ---
        pos_y_conteudo = 250
        foto_x = 60
        foto_w, foto_h = 240, 300
        
        # Caminho da foto específica do membro
        # Padrão: static/uploads/membro_ID.png (ou jpg)
        caminho_foto = os.path.join(Config.BASE_DIR, 'static', 'uploads', f'membro_{membro.id}.png')
        
        foto_carregada = False
        if os.path.exists(caminho_foto):
            try:
                user_photo = Image.open(caminho_foto).convert("RGBA")
                user_photo = user_photo.resize((foto_w, foto_h))
                img.paste(user_photo, (foto_x, pos_y_conteudo))
                foto_carregada = True
            except:
                pass
        
        # Se não tiver foto, desenha o placeholder
        if not foto_carregada:
            draw.rectangle([(foto_x, pos_y_conteudo), (foto_x + foto_w, pos_y_conteudo + foto_h)], outline=self.COR_ACCENT, width=3)
            draw.text((foto_x + 65, pos_y_conteudo + 130), "SEM FOTO", font=self._carregar_fonte(25, bold=True), fill=self.COR_TEXTO_SECUNDARIO)
        else:
            # Borda fina dourada ao redor da foto real
            draw.rectangle([(foto_x, pos_y_conteudo), (foto_x + foto_w, pos_y_conteudo + foto_h)], outline=self.COR_ACCENT, width=2)


        # --- DADOS (Direita) ---
        col_x = 340
        largura_max_texto = self.WIDTH - col_x - 50 # Limite até a borda direita
        
        font_label = self._carregar_fonte(18)
        
        def desenhar_campo(label, valor, y, espacamento=85):
            # Label
            draw.text((col_x, y), label.upper(), font=font_label, fill=self.COR_TEXTO_SECUNDARIO)
            
            # Valor (Com ajuste automático de tamanho!)
            valor_str = str(valor).upper() if valor else "-----"
            self._desenhar_texto_ajustavel(
                draw, 
                valor_str, 
                col_x, 
                y + 25, 
                max_width=largura_max_texto, 
                initial_size=40, # Começa tentando fonte 40
                color=self.COR_TEXTO_PRINCIPAL,
                bold=True
            )
            return y + espacamento

        y_cursor = pos_y_conteudo + 10
        y_cursor = desenhar_campo("NOME COMPLETO", membro.nome, y_cursor)
        y_cursor = desenhar_campo("CARGO / FUNÇÃO", membro.cargo, y_cursor)

        # Datas lado a lado
        draw.text((col_x, y_cursor), "NASCIMENTO", font=font_label, fill=self.COR_TEXTO_SECUNDARIO)
        draw.text((col_x + 300, y_cursor), "MEMBRO DESDE", font=font_label, fill=self.COR_TEXTO_SECUNDARIO)
        
        data_nasc = membro.data_nascimento.strftime('%d/%m/%Y') if membro.data_nascimento else "--/--"
        ano_atual = datetime.now().year
        
        font_data = self._carregar_fonte(32, bold=True)
        draw.text((col_x, y_cursor + 25), data_nasc, font=font_data, fill=self.COR_TEXTO_PRINCIPAL)
        draw.text((col_x + 300, y_cursor + 25), str(ano_atual), font=font_data, fill=self.COR_TEXTO_PRINCIPAL)

        # --- QR CODE (Dourado) ---
        qr_size = 140
        qr_x = self.WIDTH - qr_size - 40
        qr_y = self.HEIGHT - qr_size - 40
        
        qr = qrcode.QRCode(box_size=4, border=1)
        qr.add_data(f"ID:{membro.id}|{membro.nome}")
        qr.make(fit=True)
        # QR Code Preto e Dourado
        img_qr = qr.make_image(fill_color="black", back_color=self.COR_ACCENT)
        img_qr = img_qr.resize((qr_size, qr_size))
        
        img.paste(img_qr, (qr_x, qr_y))

        # Retornar Bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr