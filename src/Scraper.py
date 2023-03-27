from bs4 import BeautifulSoup
import logging
from python_lexmark.src.Requisicao_threads import Requisicao_threads
logging.basicConfig()
logger = logging.getLogger("Scraper")
logger.setLevel(logging.DEBUG)


class Scraper():
    def __init__(self, url_impressora: str) -> None:
        """Objeto base para raspagem dos dados da impressora

        Args:
            url_impressora (str): Endereço da impressora
        """
        self._url_impressora = url_impressora
        self._lista_bandejas = []

    def parse_pagina(self, conteudo: str) -> BeautifulSoup:
        """Transforma o conteúdo bruto da página em objeto soup

        Args:
            conteudo (str): Conteúdo da página

        Returns:
            BeautifulSoup: objeto soup pronto pra raspagem
        """
        soup = BeautifulSoup(conteudo, 'html.parser')
        return soup

    def obter_pagina(self, url):
        pass

    class ScraperErrors():
        class ElementoAusente(Exception):
            pass

        class ModeloIncompativel(Exception):
            pass

        class FalhaRequisicao(Exception):
            pass


class ScraperLexmarkMX611dhe(Scraper):
    def __init__(self, url_impressora: str) -> None:
        super().__init__(url_impressora)



