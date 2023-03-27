# python_lexmark
API não oficial para coleta de informações de impressoras Lexmark  
No momento o único modelo suportado é a MS811

## Como usar?

```python
from python_lexmark.src.ScraperLexmarkMS811 import ScraperLexmarkMS811
url = 'http://192.168.0.11' # IP da impressora, acessível pelo navegador
scraper_ms811 = ScraperLexmarkMS811(url)
```

## Quais informações estão disponíveis?
Na forma de atributos do objeto ScraperLexmarkMS811()
- modelo (str)
- status_impressora (str)
- bandeja1 (str)
- bandeja2 (str)
- bandeja_padrao (str)
- toner (int)
- kit_rolo (int)
- kit_manutencao (int)
- unidade_imagem (int)
