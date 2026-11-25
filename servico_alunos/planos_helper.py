"""fala com serviço planos via HTTP, nunca direto no banco."""
import logging
import os

import requests

PLANOS_URL = os.getenv("PLANOS_URL", "http://127.0.0.1:5002")
TEMPO_LIMITE = 5  # segundos

log = logging.getLogger(__name__)


class ServicoIndisponivel(Exception):
    pass


def buscar_plano(plano_id):
    """busca plano por id. retorna dict, None se não achar, ou lança ServicoIndisponivel."""
    url = f"{PLANOS_URL}/planos/{plano_id}"
    log.info("Consultando serviço de planos: GET %s", url)
    try:
        resposta = requests.get(url, timeout=TEMPO_LIMITE)
    except requests.exceptions.Timeout:
        log.error("Serviço de planos não respondeu em %ss", TEMPO_LIMITE)
        raise ServicoIndisponivel(f"O serviço de planos não respondeu em {TEMPO_LIMITE} segundos.")
    except requests.exceptions.ConnectionError:
        log.error("Serviço de planos fora do ar (%s)", PLANOS_URL)
        raise ServicoIndisponivel("O serviço de planos está fora do ar. Tente novamente mais tarde.")

    if resposta.status_code == 404:
        return None
    if resposta.status_code != 200:
        raise ServicoIndisponivel(f"O serviço de planos retornou erro {resposta.status_code}.")
    return resposta.json()
