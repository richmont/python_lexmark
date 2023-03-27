import queue
from threading import Thread
import logging
import requests
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Requisicao_threads():
    
    def __init__(self, lista_enderecos: list, num_threads=6) -> None:
        """Executa requisição utilizando threads para paralelismo

        Args:
            lista_enderecos (list): lista com endereços a serem requisitados
            num_threads (int, optional): Número de threads a serem usadas.
                                         Padrão são 6
        """
        self.lista_enderecos = lista_enderecos
        self._fila_enderecos = queue.Queue()
        self._fila_conteudo_paginas = queue.Queue()
        self.executar_threads(num_threads)
        self.preencher_fila_enderecos(self._fila_enderecos, lista_enderecos)
        self._fila_enderecos.join()  # aguarda fila terminar
        self.lista_conteudo_paginas = self.obter_resultados(self._fila_conteudo_paginas)

    
    def executar_requisicao(self,
                            _fila_enderecos: queue.Queue,
                            _fila_conteudo_paginas: queue.Queue) -> None:
        """Busca o conteúdo da página pelo URL

        Args:
            url (str): Endereço da página
            num_threads (int): Quantidade de threads para execução, padrão: 30

        Returns:
            str: Conteúdo da página
        """
        try:
            url = _fila_enderecos.get()
            logger.debug("Executando requisição no URL: %s", url)
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                logger.debug("Código 200 recebido, guardando conteúdo na fila")
                dict_conteudo = {"url": url, "pagina_conteudo": r.text}
                _fila_conteudo_paginas.put(dict_conteudo)
                _fila_enderecos.task_done()
            else:
                logger.debug("Requisição falhou, código de erro: %s", r.status_code)
                _fila_enderecos.task_done()
        except requests.exceptions.ReadTimeout:
            logger.error("Requisição falhou na URL %s - Tempo de espera \
esgotou", url)
            _fila_enderecos.task_done()
        except requests.exceptions.ConnectionError:
            logger.error("Requisição falhou na URL %s - Sem Conexão", url)
            _fila_enderecos.task_done()
        except requests.exceptions.MissingSchema:
            logger.error("Requisição falhou na URL %s - URL Incorreto", url)
            _fila_enderecos.task_done()

    
    def executar_threads(self, num_threads: int) -> None:
        """Executa o método executar_ping usando threads
        Args:
            num_threads (int): Número de threads a ser usada para processo
        """
        logger.debug("Iniciando execução com %i threads", num_threads)
        for x in range(1, num_threads):
            
            trabalhador = Thread(target=self.executar_requisicao, args=(self._fila_enderecos, self._fila_conteudo_paginas))
            trabalhador.setDaemon(True)
            trabalhador.start()

    
    def preencher_fila_enderecos(self, fila_enderecos: queue.Queue, lista_enderecos: list) -> None:
        """Preenche a fila com valores dos endereços a serem verificados

        Args:
            fila_enderecos (queue.Queue): Objeto fila que guarda os valores
            lista_enderecos (list): lista de enderecos recebida pelo objeto
        """
        for x in lista_enderecos:
            logger.debug("Inserindo endereço %s na fila", x)
            fila_enderecos.put(x)
        logger.debug("Concluindo inserção dos endereços, tamanho da fila: %s", str(fila_enderecos.qsize()))
        
    def obter_resultados(self, fila_respostas: queue.Queue) -> list:
        """Obtém a partir da fila de respostas
        a lista dos dicionários com o resultado do processamento

        Args:
            fila_respostas (queue.Queue): Conteúdo das páginas obtidas
            com requisições

        Raises:
            Requisicao_threads.ListaRespostasVazia: Quando lista de
            respostas não possui nenhum conteúdo

        Returns:
            list: Lista de str com conteúdo das páginas
        """
        lista_respostas = []
        while True:
            try:
                # obtém valor sem aguardar execução
                resposta = fila_respostas.get_nowait()
                if resposta is None:
                    pass
                else:
                    lista_respostas.append(resposta)
            except queue.Empty:
                logger.debug("Lista de respostas vazia, finalizando")
                break  # quebra o laço quando lista fica vazia
        if len(lista_respostas) == 0:
            raise Requisicao_threads.ListaRespostasVazia("Lista de \
respostas não possui nenhum elemento, verifique a lista")
        return lista_respostas

    class ListaRespostasVazia(Exception):
        pass


if __name__ == "__main__":
    lista_impressoras = ['http://192.168.0.1']
    scraper_threads = Requisicao_threads(lista_impressoras)
# scraper_threads.executar_scrap('http://localhost:8000/impressoras/')
# try:
#    scraper_threads.executar_requisicao('https://github.com')
# except roar.BeartypeCallHintReturnViolation:
#    pass
