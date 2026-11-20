# Academia – Arquitetura em Microsserviços (Flask)

Projeto da disciplina de **arquitetura de Software** (Unisatc).
Back-end de uma academia, dividido em quatro microsserviços feitos com Python, Flask,
Flask-SQLAlchemy e SQLite, que se comunicam por HTTP/JSON.

---

## 1. Documento de requisitos

### a) Propósito do sistema
Controlar os alunos de uma academia, os planos contratados, os instrutores e os pagamentos
das mensalidades. Assim a recepção sabe quem está **ativo** e quem está **em dia**.

### b) Usuários
- **Recepcionista / atendente:** cadastra alunos e registra pagamentos.
- **Gerente da academia:** cadastra planos e instrutores e acompanha os pagamentos.
- **Instrutor:** consulta os dados dos alunos e o plano de cada um.

### c) Requisitos funcionais
| Código | Requisito |
|---|---|
| RF01 | Cadastrar, listar, consultar, alterar e remover **planos** (nome, valor, duração em meses). |
| RF02 | Cadastrar, listar, consultar, alterar e remover **instrutores** (nome, especialidade, CREF). |
| RF03 | Cadastrar, listar, consultar, alterar e remover **alunos** (nome, e-mail, plano, instrutor, ativo). |
| RF04 | Ao cadastrar ou alterar um aluno, validar se o plano informado existe. |
| RF05 | Ao consultar um aluno, mostrar os dados do seu **plano** (e do instrutor responsável). |
| RF06 | Registrar **pagamentos** (aluno, valor, mês de referência, forma de pagamento). |
| RF07 | Ao registrar o pagamento, validar se o aluno existe e está **ativo**. |
| RF08 | Ao registrar o pagamento, o aluno passa a constar como **"em dia"**. |
| RF09 | Se o serviço de alunos falhar na etapa do RF08, o pagamento é **desfeito** (compensação). |
| RF10 | Listar os pagamentos, com filtro por aluno. |

---

## 2. Descritivo técnico

### Microsserviços

| Serviço | Pasta | Porta | Banco SQLite | Função |
|---|---|---|---|---|
| **Alunos** | `servico_alunos/` | 5001 | `alunos.db` | Cadastro de alunos, situação (ativo / em dia). Consulta Planos e Instrutores. |
| **Planos** | `servico_planos/` | 5002 | `planos.db` | Cadastro dos planos da academia (Mensal, Trimestral, Anual…). |
| **Instrutores** | `servico_instrutores/` | 5003 | `instrutores.db` | Cadastro dos instrutores. |
| **Pagamentos** | `servico_pagamentos/` | 5004 | `pagamentos.db` | Registro das mensalidades. Consulta e altera Alunos. |

Cada serviço tem:
- `app.py`: cria o app Flask, configura o banco, os logs e sobe na porta do serviço;
- `models.py`: modelo do Flask-SQLAlchemy;
- `regras.py`: validações e regras de negócio;
- `rotas.py`: rotas REST (Blueprint) que devolvem JSON;
- `<nome>_helper.py`: integração com outro serviço via `requests` (só nos serviços que chamam outro).

O banco SQLite fica em `instance/` dentro da pasta de cada serviço. Cada serviço cria
alguns dados de exemplo quando inicia com o banco vazio, o que ajuda no Render, onde o disco é apagado.

### Integrações

```
                  GET /planos/<id>   (Busca 1)
   ┌───────────┐ ─────────────────────────────▶ ┌──────────┐
   │  Alunos   │                                 │  Planos  │
   │   5001    │ ─────────────────────────────▶ └──────────┘
   └───────────┘   GET /instrutores/<id> (extra) ┌─────────────┐
        ▲  ▲      ─────────────────────────────▶ │ Instrutores │
        │  │                                      └─────────────┘
        │  │ PATCH /alunos/<id>/situacao  (Alteração)
        │  └──────────────────────────────┐
        │ GET /alunos/<id>  (Busca 2)      │
   ┌────┴───────────────────────────────── ┴┐
   │              Pagamentos 5004           │
   └────────────────────────────────────────┘
```

| # | Tipo | Quem chama → quem responde | Quando | Arquivo |
|---|---|---|---|---|
| 1 | **Busca (GET)** | Alunos → Planos | Ao consultar o aluno (`GET /alunos/<id>`), o plano é mostrado junto. Também valida o plano ao cadastrar o aluno. | `servico_alunos/planos_helper.py` |
| 2 | **Busca (GET)** | Pagamentos → Alunos | Ao registrar o pagamento, confere se o aluno existe e está ativo. | `servico_pagamentos/alunos_helper.py` |
| 3 | **Alteração (PATCH)** | Pagamentos → Alunos | Depois de salvar o pagamento, marca o aluno como `"em dia"`. | `servico_pagamentos/alunos_helper.py` |
| extra | Busca (GET) | Alunos → Instrutores | Ao consultar o aluno, mostra o instrutor responsável. | `servico_alunos/instrutores_helper.py` |

### Regras de integração atendidas
- Um serviço **nunca** acessa o banco do outro: só por HTTP.
- Só guardamos o **id** do outro serviço (`plano_id`, `instrutor_id`, `aluno_id`), sem ForeignKey entre bancos.
- Os endereços dos outros serviços vêm de **variáveis de ambiente**, com padrão local:
  `PLANOS_URL=http://127.0.0.1:5002`, `INSTRUTORES_URL=http://127.0.0.1:5003`, `ALUNOS_URL=http://127.0.0.1:5001`.
  Cada serviço também aceita `PORT` (porta) e `DATABASE_URL` (padrão `sqlite:///<servico>.db`).
- Toda chamada tem **tempo limite** (5 s). Se o outro serviço estiver fora do ar, é devolvido um **erro claro**
  (HTTP 503 com `{"erro": "..."}`), e o programa não quebra. Na Busca 1, o aluno é devolvido mesmo assim,
  com a mensagem de erro no lugar do plano.
- **Tratamento de falha na alteração:**
  - **Tentar de novo:** o PATCH para Alunos é tentado até 3 vezes, com 1 s de espera entre as tentativas.
  - **Compensação:** se as 3 tentativas falharem, o pagamento já salvo é **apagado**, e a resposta explica que ele foi desfeito.

### Observabilidade
Os logs seguem o mesmo padrão em todos os serviços: `data | nível | serviço | mensagem`. Cada requisição
recebida fica registrada, assim como cada chamada a outro serviço, cada nova tentativa e cada compensação. Exemplo:
```
2026-11-20 10:08:35,163 | INFO    | pagamentos | Consultando serviço de alunos: GET http://127.0.0.1:5001/alunos/2
2026-11-20 10:08:35,172 | INFO    | pagamentos | Pagamento 2 salvo para o aluno 2
2026-11-20 10:08:35,172 | WARNING | pagamentos | Falha na tentativa 1: o serviço de alunos está fora do ar
2026-11-20 10:08:35,173 | ERROR   | pagamentos | Compensação: removendo pagamento 2. Motivo: ...
```

### Endpoints

| Serviço | Método | Rota | Descrição |
|---|---|---|---|
| Todos | GET | `/` | Status do serviço (`{"servico": "...", "status": "ok"}`) |
| Alunos | GET | `/alunos` | Lista alunos |
| Alunos | GET | `/alunos/<id>` | Consulta aluno **+ plano + instrutor** |
| Alunos | POST | `/alunos` | Cria aluno (valida plano) |
| Alunos | PUT | `/alunos/<id>` | Altera aluno |
| Alunos | PATCH | `/alunos/<id>/situacao` | Altera situação (`"em dia"` / `"pendente"`) |
| Alunos | DELETE | `/alunos/<id>` | Remove aluno |
| Planos | GET/POST | `/planos` | Lista / cria |
| Planos | GET/PUT/DELETE | `/planos/<id>` | Consulta / altera / remove |
| Instrutores | GET/POST | `/instrutores` | Lista / cria |
| Instrutores | GET/PUT/DELETE | `/instrutores/<id>` | Consulta / altera / remove |
| Pagamentos | GET | `/pagamentos[?aluno_id=1]` | Lista pagamentos |
| Pagamentos | GET/DELETE | `/pagamentos/<id>` | Consulta / remove |
| Pagamentos | POST | `/pagamentos` | Registra pagamento (**Busca 2 + Alteração**) |

Exemplos de corpo:
```jsonc
// POST /planos
{ "nome": "Semestral", "valor": 499.90, "duracao_meses": 6 }
// POST /instrutores
{ "nome": "Marcos Dias", "especialidade": "Pilates", "cref": "011223-G/SC" }
// POST /alunos  (plano_id obrigatório; instrutor_id e ativo opcionais)
{ "nome": "Diego Alves", "email": "diego@email.com", "plano_id": 1, "instrutor_id": 2, "ativo": true }
// PATCH /alunos/<id>/situacao
{ "situacao_pagamento": "em dia", "pagamento_id": 1 }
// POST /pagamentos  (forma: pix | cartao | dinheiro | boleto — padrão pix)
{ "aluno_id": 1, "valor": 99.90, "referencia": "2026-11", "forma": "pix" }
```

### Códigos de resposta
Os erros sempre voltam no formato `{"erro": "mensagem"}`.

| Código | Quando |
|---|---|
| 200 / 201 | Sucesso (201 nas criações) |
| 400 | JSON ausente ou campo inválido / obrigatório faltando |
| 404 | Registro não encontrado (inclusive aluno inexistente ao registrar pagamento) |
| 422 | Plano inexistente ao cadastrar/alterar aluno; aluno **inativo** ao registrar pagamento |
| 503 | Outro serviço fora do ar ou sem resposta em 5 s (com compensação, quando for o caso) |

### Dados iniciais
- Planos: 1 Mensal (R$ 99,90), 2 Trimestral (R$ 269,90), 3 Anual (R$ 899,90)
- Instrutores: 1 Carlos Souza (Musculação), 2 Fernanda Lima (Funcional)
- Alunos: 1 Ana (ativa), 2 Bruno (ativo), 3 Camila (**inativa**, usada para testar a Busca 2)

---

## 3. Como executar localmente

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

Abra **4 terminais** no VS Code, um para cada serviço:
```bash
cd servico_alunos      && python app.py   # porta 5001
cd servico_planos      && python app.py   # porta 5002
cd servico_instrutores && python app.py   # porta 5003
cd servico_pagamentos  && python app.py   # porta 5004
```

## 4. Demonstração (Thunder Client)

Importe `thunder-client/thunder-collection_academia.json` no Thunder Client
(menu *Collections → ⋮ → Import*). A coleção tem uma pasta por serviço (CRUD) e a pasta **Integrações**:

1. **Busca 1:** `GET /alunos/1` devolve o aluno com o objeto `plano`.
2. **Busca 2:** pagamento do aluno 3 (inativo) devolve **422**.
3. **Busca 2 + Alteração:** pagamento do aluno 1 devolve **201**, e o aluno passa a `"situacao_pagamento": "em dia"`.
4. **Falha:** pare o serviço de Alunos (Ctrl+C) e registre um pagamento: a resposta é **503** com uma mensagem clara,
   e o programa continua no ar.
5. **Nova tentativa e compensação:** se o Alunos cair entre a Busca 2 e a Alteração, o log de Pagamentos mostra
   as 3 tentativas do PATCH e a remoção do pagamento salvo (`Compensação: removendo pagamento ...`), e a resposta
   explica que o pagamento foi desfeito.

## 5. Publicação no Render

Crie **4 Web Services** no Render, um por pasta, com:

| Campo | Valor |
|---|---|
| Root Directory | `servico_alunos` (ou `servico_planos`, `servico_instrutores`, `servico_pagamentos`) |
| Build Command | `pip install -r ../requirements.txt` |
| Start Command | `gunicorn app:app` |

Variáveis de ambiente (use as **URLs públicas** de cada serviço):
- `servico_alunos`: `PLANOS_URL=https://<planos>.onrender.com`, `INSTRUTORES_URL=https://<instrutores>.onrender.com`
- `servico_pagamentos`: `ALUNOS_URL=https://<alunos>.onrender.com`

O Render define a variável `PORT` sozinho. Lembre de "acordar" os serviços (abrir `/` de cada um) antes da demonstração.

## Estrutura

```
├── servico_alunos/       app.py, models.py, regras.py, rotas.py, planos_helper.py, instrutores_helper.py
├── servico_planos/       app.py, models.py, regras.py, rotas.py
├── servico_instrutores/  app.py, models.py, regras.py, rotas.py
├── servico_pagamentos/   app.py, models.py, regras.py, rotas.py, alunos_helper.py
├── thunder-client/       thunder-collection_academia.json
├── requirements.txt
└── README.md
```
