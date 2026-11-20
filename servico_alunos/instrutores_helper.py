"""Integração com o serviço de Instrutores (via HTTP, nunca pelo banco)."""
import logging
import os

import requests

INSTRUTORES_URL = os.getenv("INSTRUTORES_URL", "http://127.0.0.1:5003")
TEMPO_LIMITE = 5  # segundos

log = logging.getLogger(__name__)


class ServicoIndisponivel(Exception):
    pass


def buscar_instrutor(instrutor_id):
    """Retorna o instrutor (dict), None se não existir, ou lança ServicoIndisponivel."""
    url = f"{INSTRUTORES_URL}/instrutores/{instrutor_id}"
    log.info("Consultando serviço de instrutores: GET %s", url)
    try:
        resposta = requests.get(url, timeout=TEMPO_LIMITE)
    except requests.exceptions.Timeout:
        log.error("Serviço de instrutores não respondeu em %ss", TEMPO_LIMITE)
        raise ServicoIndisponivel(f"O serviço de instrutores não respondeu em {TEMPO_LIMITE} segundos.")
    except requests.exceptions.ConnectionError:
        log.error("Serviço de instrutores fora do ar (%s)", INSTRUTORES_URL)
        raise ServicoIndisponivel("O serviço de instrutores está fora do ar. Tente novamente mais tarde.")

    if resposta.status_code == 404:
        return None
    if resposta.status_code != 200:
        raise ServicoIndisponivel(f"O serviço de instrutores retornou erro {resposta.status_code}.")
    return resposta.json()
