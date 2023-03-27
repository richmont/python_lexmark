from bs4 import BeautifulSoup
import logging
from python_lexmark.src.Requisicao_threads import Requisicao_threads
from python_lexmark.src.Scraper import Scraper
import re

logging.basicConfig()
logger = logging.getLogger("ScraperLexmarkMS811")
logger.setLevel(logging.DEBUG)

class ScraperLexmarkMS811(Scraper):
    def __init__(self, url_impressora: str) -> None:
        """Detecta informações de impressoras Lexmark modelo MS811
        através de sua página web.
        Nível de suprimento de bandejas e Status atuais, realiza requisições com threads

        Args:
            url_impressora (str): Endereço da página web de status da impressora
                                  Usualmente no padrão: "http://192.168.0.1"
                                  Onde este IP é o configurado para a impressora

        Raises:
            Scraper.ScraperErrors.FalhaRequisicao: Falha ao obter página web da impressora
            Scraper.ScraperErrors.ModeloIncompativel: Modelo detectado da impressora é incompatível
            Scraper.ScraperErrors.ElementoAusente: Elemento da página necessário para coleta do suprimento das bandejas está ausente
        """
        super().__init__(url_impressora)
        url_base = self._url_impressora
        self.bandeja1 = str()
        self.bandeja2 = str()
        self.bandeja_padrao = str()
        self.toner = int()

        try:
            pagina_soup = self.obter_pagina(url_base)
            self.soup_topbar = pagina_soup["topbar"]
            self.soup_status = pagina_soup["status"]

        except Requisicao_threads.ListaRespostasVazia:
            raise Scraper.ScraperErrors.FalhaRequisicao(f"Requisição da impressora no IP {url_impressora} falhou, verifique o endereço")
        self.modelo = self.raspar_modelo(self.soup_topbar)

        self.status_impressora = self.status_atual(self.soup_topbar)

        self.nivel_papel(self.soup_status)
        self.toner = self.nivel_toner(self.soup_status)
        self.kit_rolo = self.nivel_kit_rolo(self.soup_status)
        self.kit_manutencao = self.nivel_kit_manutencao(self.soup_status)
        self.unidade_imagem = self.nivel_unidade_imagem(self.soup_status)

    def obter_pagina(self, url_base: str) -> dict:
        """Através de um objeto de requisição, obtém o conteúdo
        das páginas necessárias para coleta de dados

        Args:
            url_base (str): URL base, o restante do endereço é gerado

        Returns:
            (dict): {
                        status: Conteúdo do frame de status
                        topbar: Conteúdo do frame topbar, o cabeçalho da página
                    }
        """
        sufixo_status = "/cgi-bin/dynamic/printer/PrinterStatus.html"
        sufixo_topbar = "/cgi-bin/dynamic/topbar.html"
        url_status = f"{url_base}{sufixo_status}"
        url_topbar = f"{url_base}{sufixo_topbar}"
        lista_enderecos = [url_status, url_topbar]

        t_requisicao = Requisicao_threads(lista_enderecos)

        for x in t_requisicao.lista_conteudo_paginas:
            if x["url"] == url_status:
                conteudo_status = x["pagina_conteudo"]
            elif x["url"] == url_topbar:
                conteudo_topbar = x["pagina_conteudo"]

        soup_status = self.parse_pagina(conteudo_status)
        soup_topbar = self.parse_pagina(conteudo_topbar)
        return {"status": soup_status, "topbar": soup_topbar}

    def raspar_modelo(self, soup_topbar: BeautifulSoup) -> str:
        """Verifica modelo da impressora

        Args:
            soup_topbar (BeautifulSoup): sopa da página \
"topbar" a ser analisada

        Raises:
            Scraper.ModeloIncompativel: Modelo detectado é diferente do \
suportado pelo scraper

        Returns:
            str: Modelo da impressora em uma string
        """
        modelo_tag = soup_topbar.find_all("span", {"class": "top_prodname"})
        modelo = modelo_tag[0].text
        if modelo == "Lexmark MS811":
            return modelo
        else:
            raise Scraper.ScraperErrors.ModeloIncompativel("Modelo de impressora detectado\
                 não é compatível: %s", modelo)

    def nivel_papel(self, soup_status: BeautifulSoup) -> None:
        """Obtém o nível de papel nas bandejas da impressora

        Args:
            soup_status (BeautifulSoup): Sopa com elementos da página Status

        Raises:
            ScrapersErrors.ElementoAusente: Elemento de nível da bandeja não encontrado na página

        """
        lista_bandejas = []

        tags_paper = soup_status.find_all("table", {"style": "padding: .75pt"})

        for x in tags_paper:
            # extrai o conteúdo de hierarquia de tags
            lista_bandejas.append(x.tr.td.b.text)

        # armazena o conteúdo de lista de tags
        try:
            self.bandeja1 = lista_bandejas[0]
        except IndexError:
            raise Scraper.ScraperErrors.ElementoAusente('bandeja1')
        try:
            self.bandeja2 = lista_bandejas[1]
        except IndexError:
            raise Scraper.ScraperErrors.ElementoAusente('bandeja2')
        try:
            self.bandeja_padrao = lista_bandejas[2]
        except IndexError:
            raise Scraper.ScraperErrors.ElementoAusente('bandeja_padrao')

    def status_atual(self, soup_topbar: BeautifulSoup) -> str:
        status_impressora_tag = soup_topbar.find_all("td", {"class": "statusLine"})
        statusline = status_impressora_tag[0].font.text.replace("Ã£","ã")
        return statusline

    def nivel_toner(self, soup_status: BeautifulSoup) -> int:
        """Obtém da sopa Status o valor do nível de toner da impressora

        Args:
            soup_status (BeautifulSoup): sopa da página de Status da impressora

        Returns:
            int: Valor numérico do nível de toner
        """
        tag_toner = soup_status.find_all("td", {"colspan": "4"})
        texto_toner = tag_toner[1].b.text
        metade_final = texto_toner.split("~")
        valor_numerico = metade_final[1].strip("%")
        return int(valor_numerico)

    def nivel_kit_manutencao(self, soup_status) -> int:
        """Obtém da sopa Status o valor do nível de kit de manutenção da impressora

        Args:
            soup_status (BeautifulSoup): sopa da página de Status da impressora

        Returns:
            int: Valor numérico do nível de kit de manutenção
        """
        tag_kits = soup_status.find_all("table", {"class", "status_table"})
        tag_kit_manutencao = tag_kits[3].find(string=re.compile('Kit'))
        return int(tag_kit_manutencao.next_element.text.strip("%"))

    def nivel_kit_rolo(self, soup_status: BeautifulSoup) -> int:
        """Obtém da sopa Status o valor do nível de kit do rolo da impressora

        Args:
            soup_status (BeautifulSoup): sopa da página de Status da impressora

        Returns:
            int: Valor numérico do nível de kit do rolo
        """
        tag_kits = soup_status.find_all("table",{"class", "status_table"})
        tag_kit_roll = tag_kits[3].find(string=re.compile('Kit do rolo Vida restante:'))

        return int(tag_kit_roll.next_element.text.strip("%"))

    def nivel_unidade_imagem(self, soup_status: BeautifulSoup) -> int:
        """Obtém da sopa Status o valor do nível de unidade de imagem da impressora

        Args:
            soup_status (BeautifulSoup): sopa da página de Status da impressora

        Returns:
            int: Valor numérico do nível de unidade de imagem
        """
        tag_unidade_imagem = soup_status.find_all("table",{"class", "status_table"})
        tag_image_unit = tag_unidade_imagem[3].find(string=re.compile('Unid. imagem Vida restante:'))
        return tag_image_unit.next_element.text.strip("%")


if __name__ == "__main__":
    url = "http://192.168.0.11"
    scraper_ms811 = ScraperLexmarkMS811(url)
    print(scraper_ms811.modelo)
    print(scraper_ms811.status_impressora)
    print("Bandeja 1: ", scraper_ms811.bandeja1)
    print("Bandeja 2: ", scraper_ms811.bandeja2)
    print("Bandeja Padrão: ", scraper_ms811.bandeja_padrao)
    print("Toner: ", scraper_ms811.toner)
    print("Kit Rolo: ", scraper_ms811.kit_rolo)
    print("Kit Manutenção: ", scraper_ms811.kit_manutencao)
    print("Unidade de Imagem: ", scraper_ms811.unidade_imagem)
