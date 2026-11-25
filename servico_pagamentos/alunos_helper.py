"""fala com serviço alunos via HTTP, nunca direto no banco."""
import logging
import os
import time

import requests

ALUNOS_URL = os.getenv("ALUNOS_URL", "http://127.0.0.1:5001")
TEMPO_LIMITE = 5
TENTATIVAS = 3
ESPERA_ENTRE = 1

log = logging.getLogger(__name__)


class ServicoIndisponivel(Exception):
    pass


def buscar_aluno(aluno_id):
    """busca aluno por id. retorna dict, None se não achar, ou lança ServicoIndisponivel."""
    url = f"{ALUNOS_URL}/alunos/{aluno_id}"
    log.info("Consultando serviço de alunos: GET %s", url)
    try:
        resposta = requests.get(url, timeout=TEMPO_LIMITE)
    except requests.exceptions.Timeout:
        log.error("Serviço de alunos não respondeu em %ss", TEMPO_LIMITE)
        raise ServicoIndisponivel(f"O serviço de alunos não respondeu em {TEMPO_LIMITE} segundos.")
    except requests.exceptions.ConnectionError:
        log.error("Serviço de alunos fora do ar (%s)", ALUNOS_URL)
        raise ServicoIndisponivel("O serviço de alunos está fora do ar. Tente novamente mais tarde.")

    if resposta.status_code == 404:
        return None
    if resposta.status_code != 200:
        raise ServicoIndisponivel(f"O serviço de alunos retornou erro {resposta.status_code}.")
    return resposta.json()


def marcar_em_dia(aluno_id, pagamento_id):
    """marca aluno 'em dia' no serviço alunos. tenta até TENTATIVAS vezes."""
    url = f"{ALUNOS_URL}/alunos/{aluno_id}/situacao"
    corpo = {"situacao_pagamento": "em dia", "pagamento_id": pagamento_id}
    ultimo_erro = "erro desconhecido"

    for tentativa in range(1, TENTATIVAS + 1):
        log.info("Alterando situação do aluno: PATCH %s (tentativa %s/%s)", url, tentativa, TENTATIVAS)
        try:
            resposta = requests.patch(url, json=corpo, timeout=TEMPO_LIMITE)
            if resposta.status_code == 200:
                return resposta.json()
            ultimo_erro = f"o serviço de alunos retornou erro {resposta.status_code}"
            if resposta.status_code < 500:
                break  # erro de pedido (4xx), retry não resolve
        except requests.exceptions.Timeout:
            ultimo_erro = f"o serviço de alunos não respondeu em {TEMPO_LIMITE} segundos"
        except requests.exceptions.ConnectionError:
            ultimo_erro = "o serviço de alunos está fora do ar"

        log.warning("Falha na tentativa %s: %s", tentativa, ultimo_erro)
        if tentativa < TENTATIVAS:
            time.sleep(ESPERA_ENTRE)

    raise ServicoIndisponivel(f"Não foi possível marcar o aluno como 'em dia': {ultimo_erro}.")
