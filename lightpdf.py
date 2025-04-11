from fpdf import FPDF  # type: ignore
from PIL import Image


class LigthPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_page()
        self.set_font('Helvetica', '', 10)
        self.set_margins(20, 20, 20)
        self.set_xy(20, 20)

    # Retorna o limite vertical para quebra de página
    def get_max_y(self):
        return self.h - self.t_margin - self.b_margin

    # Retorna o limite horizontal para ultrapassar margem direita
    def get_max_x(self):
        return self.w - 2 * self.l_margin

    # Renderiza uma imagem no PDF e coloca o cursor abaixo dela
    def renderImage(self, filename, prop_w=None, align=None, y_adic_new_page=None, coord=None):  # noqa: E501
        """
        Define uma imagem no PDF e coloca o cursor abaixo dela. O tamanho da
        imagem deve ser definido em relação à largura da página (parâmetro
        'prop_w') e alinhado conforme o parâmetro 'align'. Alternativamente
        pode ser informada a tupla 'coord' com as coordenadas x e y do canto
        superior esquerdo da imagem e com a largura desejada em mm

        Args:
          - filename (obrigatório): Caminho/nome do arquivo da imagem
          - prop_w (opcional): valor entre 0 e 100 que corresponde ao
          percentual da largura da página que a imagem deve ocupar.
          Sua altura é automaticamente definida com base na proporção
          entre altura e largura da própria imagem. Se não for informado,
          usa 100% da largura da página
          - align (opcional): alinhamento da imagem que pode ser 'C', 'L'
          ou 'R'. Se não for informado alinha ao centro
          - y_adic_new_page (opcional): incremento para a posição vertical,
          caso a imagem ultrapasse a margem inferior da página e seja
          renderizada na próxima página
          - coord (opcional): tupla com as coordenadas do canto superior
          esquerdo da imagem e sua largura em mm. Se for informada
          desconsidera 'prop_w' e 'align'
        """

        # Posição vertical atual do cursor
        y = self.get_y()

        # Instanciando objeto Image a partir do caminho da imagem
        img = Image.open(filename)

        # Capturando as dimensões da imagem em pixels
        W_img, H_img = img.size

        # Razão entre largura e altura
        W_H = W_img/H_img

        # Largura da página descontando as margens
        W_pg = self.w - self.l_margin - self.r_margin

        # Tupla 'coord' com posições x e y da imagem e sua largura
        # foi informada. Renderizando imagem com essas informações
        if coord is not None and type(coord) is tuple:
            # Distância entre o cursor e limite direito da página
            w_pg_disp = self.w - self.l_margin - self.r_margin

            # Altura da imagem em relação à largura informada na tupla
            h_img = coord[2] / W_H

            # Flag para indicar se não ultrapassa margem direita
            fit_rigth_margin = coord[2] <= w_pg_disp

            # Flag para indicar se não ultrapassa margem inferior
            fit_bottom_margin = coord[1] + h_img <= self.b_margin

            if fit_rigth_margin and fit_bottom_margin:
                self.image(filename, coord[0], coord[1], coord[2], h_img)
            else:
                msg = 'Detectado(s) o(s) seguinte(s) erro(s):\n'
                msg += 'Largura da imagem excede margem direita\n' if not fit_bottom_margin else ''  # noqa: E501
                msg += 'Altura da imagem excede margem inferior'
                raise ValueError(msg)  # noqa: E501

        # Não foi informada tupla. Renderizando imagem com base em 'prop_w'
        else:
            # Dimensões da imagem em milímetros
            if prop_w is None:
                prop_w = 100

            # Validando se prop_w é um valor numérico entre 0 e 100
            try:
                if prop_w < 0:
                    raise ValueError('"prop_w" não pode ser negativo')
                W_img = W_pg * prop_w / 100
            except Exception:
                raise ValueError('"prop_w" deve ser uma valor numérico entre 0 e 100')  # noqa: E501

            H_img = W_img / W_H

            # Coordenada y que é o limite para ultrapassar a margem inferior
            Y_lim = self.h - self.b_margin

            # Coordenada y da base da imagem na página
            Y = y + H_img

            # Se a base da imagem ultrapassar a margem inferior, quebra a página  # noqa: E501
            # Posição y da base da imagem na página
            if Y > Y_lim:
                self.add_page(same=True)

                # Verificando se 'y_adic_new_page' fará com que a imagem ultrapasse  # noqa: E501
                # a margem inferior
                if self.t_margin + y_adic_new_page + H_img > Y_lim:
                    msg = 'A altura da imagem ultrapassa a margem inferior. Reduza'  # noqa: E501
                    msg += ' o valor de prop_w ou de y_adic_new_page'
                    raise Exception(msg)

                y = self.t_margin if y_adic_new_page is None else y_adic_new_page + self.t_margin  # noqa: E501

            # Posicionando o cursor de acordo com o parâmetro 'align'
            match align:
                case 'L':
                    x_img = self.l_margin
                case 'R':
                    x_img = self.w - self.r_margin - W_img
                case 'C':
                    x_img = self.l_margin + \
                        (self.w - self.l_margin - self.r_margin - W_img) / 2
                case _:
                    x_img = self.l_margin + \
                        (self.w - self.l_margin - self.r_margin - W_img) / 2
                    self.set_x(x_img)

            # Renderizando a imagem de acordo com a largura
            self.image(filename, w=W_img, y=y, x=x_img)

            # Posicionando o cursor abaixo da imagem
            self.set_y(y + H_img)

    def cellBreakLine(self, txt, w, h):
        """
        Verifica se o texto 'txt' deve quebrar página ao ser renderizado em
        uma célula com multi_cell(). Retorna True se deve quebrar página ou
        False caso contrário

        Argumentos:
        - txt: o texto ou string a ser renderizado
        - w: largura da célula
        - h: altura da célula
        """

        # A largura informada foi 0 (zero, toda a largura útil da página).
        # A largura nos cálculos deve ser calculada: h - l_margn - r_margin
        if w == 0:
            w = self.w - self.l_margin - self.r_margin

        # Posição vertical inicial
        y_0 = self.get_y()

        # Limite vertical para quebra de página (altura total da folha menos
        # a margem inferior)
        y_max = self.h - self.b_margin

        # Lista com o conteúdo do texto em linhas
        lines = []

        # String com a linha atual
        line_current = ''

        # Quebrando o texto em uma lista de palavras
        words = str(txt).split()

        for word in words:
            # Adiciona à linha atual mais uma palavra do texto se não exceder a
            # largura da célula
            if self.get_string_width(line_current + ' ' + word) < w:
                line_current += ' ' + word
            # Excedeu a largura da célula. Adiciona a linha atual à lista de
            # inhas e a palavra excedente é atribuída à nova linha atual
            else:
                lines.append(line_current)
                line_current = word

        # Após o loop, caso a última palavra não tenha excedido a largura
        # da linha adcionando a última linha atual à lista de linhas
        lines.append(line_current)

        # Calculando o número de linhas. É adicionado um incremento de 1 por
        # segurança
        num_lines = len(lines) + 1

        # Altura da célula
        height_cell = num_lines * h

        # Calculando a posição y referente à base da célula
        y = y_0 + height_cell

        # Retorna True se deve quebrar linha (se y atual for maior que y_max),
        # False caso contrário
        return y > y_max

    def rowBreakLine(self, row, cols_w, h):
        """
        Verifica se a lista com strings 'row' ao ser renderizada com
        'renderRowTable()' deve quebrar página. Retorna True se deve
        quebrar página ou False caso contrário

        Argumentos:
        - row: lista com as strings de cada célula
        - cols_w: lista com as larguras das colunas em mm.
        - h: altura de uma linha sem quebra de linha
        """
        for i in range(len(row)):
            if self.cellBreakLine(row[i], cols_w[i], h):
                return True
        return False

    def renderRowTable(self, row, cols_w=[], h=5, cabec=False):
        """
        Renderiza uma linha de tabela dados os valores de cada célula em uma
        lista

        Argumentos:
        - row: iterável com os valores de cada célula
        - cols_w: lista com as larguras das colunas em mm. Se não for
        fornecido, divide a largura últil da página por igual entre as colunas
        - h: altura da linha. Usa 5 mm se não for informado
        """

        # Lista com as larguras das colunas não informadas. Distribui por igual
        if cols_w == [] or len(cols_w) < len(row):
            w_pg = self.w - self.l_margin - self.r_margin
            # Resetando a lista caso tenha sido informada com tamanho
            # diferente de row
            cols_w = []
            for i in range(len(row)):
                cols_w.append(w_pg/len(row))

        # A linha é o cabeçalho da tabela. Fonte será em negrito
        if cabec:
            self.set_font('helvetica', 'B')

        # Posição vertical inicial
        y_0 = self.get_y()

        # Altura provisória da linha
        h_temp = 0

        # Altura definitiva da linha
        h_efet = 0

        # Posição horizontal antes de se fazer qualquer coisa
        x_0 = self.get_x()

        # Posição horizontal de qualquer célula
        x = x_0

        # Renderizando a linha com tudo transparente para determinar a altura
        # efetiva da linha
        self.set_text_color(255)
        for i in range(len(row)):
            self.set_xy(x, y_0)
            self.multi_cell(cols_w[i], h, str(row[i]), border=0, align='J')
            x += cols_w[i]
            y_atual = self.get_y()
            h_temp = y_atual - y_0
            if h_efet < h_temp:
                h_efet = h_temp

        # Renderizando em definitivo apenas o texto, sem as bordas
        self.set_text_color(0)
        x = x_0
        for i in range(len(row)):
            self.set_xy(x, y_0)
            self.multi_cell(cols_w[i], h, str(row[i]), border=0, align='J')
            x += cols_w[i]

        # Renderizando em definitivo as bordas com a altura calculada
        x = x_0
        for i in range(len(row)):
            self.set_xy(x, y_0)
            self.multi_cell(cols_w[i], h_efet, '', border=1)
            x += cols_w[i]

        self.set_font('helvetica', '')
        self.set_xy(x_0, y_0 + h_efet)

    # Renderiza uma tabela a partir de uma DataFrame Pandas
    def renderTableFromPandas(self, df, options={}):
        """ renderTableFromPandas(df, options): Renderiza uma tabela a partir
        de um DataFrame Pandas.

        Args:
          df: DataFrame Pandas com os dados da tabela
          options: Dicionário com os parâmetros da tabela. As seguintes chaves
          devem ser informadas no dicionário options:
          - 'h' (opcional): altura mínima de cada linha. Se não for informado
          usa h = 5
          - 'cols' (opcional): lista com os nomes das colunas selecionadas
          de 'df'. Se não for definida usa todas as colunas
          - 'tbl_w_per' (optional): largura da tabela em percentual da largura
          da página. Se não for informada usa 100% da largura útil da página
          - 'labels' (optinal): lista com os rótulos da tabela. Se não for
          informado usa 'cols'
          - 'cols_w' (optional): lista com as larguras das colunas em % da
          largura da tabela. Usa 100% se não for informado
          - 'align' (opcional): alinhamento da tabela. Pode ser 'L', 'C' ou
          'R'. Se for omitido, alinha ao centro

        """

        # Carregando a altura mínima das linhas da tabela
        h = options.get('h', 5)

        # Carregando lista com as colunas que serão usadas do DataFrame 'df'
        cols = options.get('cols', None)
        # Não foram definidas as colunas. Usa todas
        if cols is None:
            cols = df.columns

        # Carregando lista com os rótulos da tabela. Se for nula, usa a
        # lista 'cols'
        labels = options.get('labels', cols)

        # Carregando a largura percentual da tabela em relação à largura
        # da página
        w_tab = options.get('tbl_w_per', None)

        # Se a largura percentual da tabela for nula, usa 100% da largura
        # da página subtraída das margens laterais
        if w_tab is None:
            w_tab = self.w - self.l_margin - self.r_margin
        else:
            # Largura da tabela em milímetros
            w_tab = (w_tab / 100) * (self.w - self.l_margin - self.r_margin)

        # Definindo a lista com largura das colunas em mm. Se não for definida,
        # distribui por igual
        cols_w = options.get('cols_w', None)
        if cols_w is None:
            w = w_tab / len(cols)
            cols_w = []
            for item in cols:
                cols_w.append(w)
        elif sum(cols_w) != 100:
            raise ValueError(
                'O somatório das larguras das colunas não é igual a 100%')
        else:
            for i in range(len(cols_w)):
                cols_w[i] = (cols_w[i] / 100) * w_tab

        # Extraindo os valores do dataframe para uma lista. Cada registro é uma
        # lista com os valores de cada linha
        df = df.loc[:, cols]
        lista = df.values.tolist()

        # Renderizando o cabeçalho da tabela
        # Linha vai quebrar página
        if self.rowBreakLine(labels, cols_w, h):
            self.add_page(same=True)
            self.set_xy(self.l_margin, self.t_margin)
            self.renderRowTable(labels, cols_w, cabec=True)
        # Linha não vai quebrar paǵina
        else:
            self.renderRowTable(labels, cols_w, cabec=True)

        # y = self.get_y()

        i = -1
        # Renderizando as linhas da tabela
        for row in lista:
            # Linha vai quebrar página. Adicionando nova página e
            # ajustando margens
            if self.rowBreakLine(row, cols_w, h):
                self.add_page(same=True)
                self.set_xy(self.l_margin, self.t_margin)
                self.renderRowTable(labels, cols_w, cabec=True)
            self.renderRowTable(row, cols_w, cabec=False)

    def smart_multi_cell(self, w, h, txt, border=0, align='J', fill=False, new_x='LMARGIN', new_y='NEXT'):  # noqa: E501
        """
        Escreve célula quebrando a linha caso a string 'txt' exceda a
        largura da célula. Se a célula exceder a margem inferior,
        insere uma nova página e escreve no topo dessa nova página
        """

        # String 'txt' vai quebrar página
        if self.cellBreakLine(str(txt), w, h):
            self.add_page(same=True)

        self.multi_cell(w, h, str(txt), border, align,
                        fill, new_x=new_x, new_y=new_y)
