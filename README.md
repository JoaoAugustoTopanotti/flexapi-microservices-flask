# Academia - Arquitetura em Microsserviços (Flask)

Back-end de uma academia dividido em quatro microsserviços (Python, Flask, Flask-SQLAlchemy, SQLite), comunicando-se por HTTP/JSON.

## 1. Documento de requisitos

### Propósito

Controlar alunos, planos contratados, instrutores e pagamentos de mensalidades, permitindo à recepção saber quem está ativo e quem está em dia.

### Usuários

- Recepcionista: cadastra alunos e registra pagamentos.
- Gerente: cadastra planos e instrutores, acompanha pagamentos.
- Instrutor: consulta dados dos alunos e seus planos.

### Requisitos funcionais

- RF01: CRUD de planos (nome, valor, duração em meses)
- RF02: CRUD de instrutores (nome, especialidade, CREF)
- RF03: CRUD de alunos (nome, e-mail, plano, instrutor, situação ativo)
- RF04: validar existência do plano ao cadastrar/alterar aluno
- RF05: exibir dados do plano e do instrutor ao consultar um aluno
- RF06: registrar pagamentos (aluno, valor, referência, forma)
- RF07: validar que o aluno existe e está ativo ao registrar pagamento
- RF08: marcar aluno como "em dia" ao registrar pagamento
- RF09: desfazer o pagamento (compensação) se a marcação do RF08 falhar
- RF10: listar pagamentos, com filtro por aluno

## 2. Descritivo técnico

### Microsserviços

- Alunos (servico_alunos, porta 5001, banco alunos.db): cadastro e situação dos alunos; consulta planos e instrutores.
- Planos (servico_planos, porta 5002, banco planos.db): cadastro dos planos da academia.
- Instrutores (servico_instrutores, porta 5003, banco instrutores.db): cadastro dos instrutores.
- Pagamentos (servico_pagamentos, porta 5004, banco pagamentos.db): registro de mensalidades; consulta e altera alunos.

Cada serviço segue a mesma estrutura:
- `app.py`: configuração do Flask, do banco, dos logs e inicialização.
- `models.py`: modelo Flask-SQLAlchemy.
- `regras.py`: validações e regras de negócio.
- `rotas.py`: rotas REST (Blueprint) em JSON.
- `<nome>_helper.py`: integração HTTP com outro serviço (apenas nos serviços que chamam outro).

O banco SQLite fica em `instance/` dentro de cada pasta. Cada serviço popula dados de exemplo ao iniciar com o banco vazio, útil para o deploy no Render (disco temporário).

### Integrações

1. GET, Alunos → Planos: ao consultar ou cadastrar aluno, valida/retorna o plano (servico_alunos/planos_helper.py).
2. GET, Pagamentos → Alunos: ao registrar pagamento, valida existência e situação ativa (servico_pagamentos/alunos_helper.py).
3. PATCH, Pagamentos → Alunos: após salvar o pagamento, marca o aluno como "em dia" (servico_pagamentos/alunos_helper.py).
4. GET, Alunos → Instrutores: ao consultar aluno, retorna o instrutor responsável (servico_alunos/instrutores_helper.py).

### Regras de integração

- Nenhum serviço acessa o banco de outro: comunicação só por HTTP.
- Apenas o id do recurso remoto é armazenado (`plano_id`, `instrutor_id`, `aluno_id`), sem ForeignKey entre bancos.
- Endereços configuráveis por variável de ambiente, com padrão local:
  `PLANOS_URL=http://127.0.0.1:5002`, `INSTRUTORES_URL=http://127.0.0.1:5003`, `ALUNOS_URL=http://127.0.0.1:5001`.
  Cada serviço também lê `PORT` e `DATABASE_URL` (padrão `sqlite:///<servico>.db`).
- Toda chamada tem timeout de 5s. Se o serviço remoto estiver indisponível, retorna 503 com `{"erro": "..."}` sem derrubar o processo. Na busca de aluno (item 1), o aluno é retornado mesmo assim, com a mensagem de erro no lugar do plano.
- Tratamento de falha na alteração (item 3):
  - Retry: até 3 tentativas, com 1s de intervalo.
  - Compensação: se todas as tentativas falharem, o pagamento já salvo é removido e a resposta informa o desfazimento.

### Observabilidade

Logs padronizados em todos os serviços: `data | nível | serviço | mensagem`. Registram cada requisição recebida, cada chamada a outro serviço, cada nova tentativa e cada compensação.

Exemplo:
```
2026-11-20 10:08:35,163 | INFO    | pagamentos | Consultando serviço de alunos: GET http://127.0.0.1:5001/alunos/2
2026-11-20 10:08:35,172 | INFO    | pagamentos | Pagamento 2 salvo para o aluno 2
2026-11-20 10:08:35,172 | WARNING | pagamentos | Falha na tentativa 1: o serviço de alunos está fora do ar
2026-11-20 10:08:35,173 | ERROR   | pagamentos | Compensação: removendo pagamento 2. Motivo: ...
```

### Endpoints

Todos os serviços: GET / retorna o status.

Alunos:
- GET /alunos - lista alunos
- GET /alunos/<id> - consulta aluno, plano e instrutor
- POST /alunos - cria aluno (valida plano)
- PUT /alunos/<id> - altera aluno
- PATCH /alunos/<id>/situacao - altera situação de pagamento
- DELETE /alunos/<id> - remove aluno

Planos:
- GET/POST /planos - lista / cria
- GET/PUT/DELETE /planos/<id> - consulta / altera / remove

Instrutores:
- GET/POST /instrutores - lista / cria
- GET/PUT/DELETE /instrutores/<id> - consulta / altera / remove

Pagamentos:
- GET /pagamentos[?aluno_id=1] - lista pagamentos
- GET/DELETE /pagamentos/<id> - consulta / remove
- POST /pagamentos - registra pagamento (busca 2 + alteração)

Exemplos de corpo:

```jsonc
// POST /planos
{ "nome": "Semestral", "valor": 499.90, "duracao_meses": 6 }

// POST /instrutores
{ "nome": "Marcos Dias", "especialidade": "Pilates", "cref": "011223-G/SC" }

// POST /alunos (plano_id obrigatório; instrutor_id e ativo opcionais)
{ "nome": "Diego Alves", "email": "diego@email.com", "plano_id": 1, "instrutor_id": 2, "ativo": true }

// PATCH /alunos/<id>/situacao
{ "situacao_pagamento": "em dia", "pagamento_id": 1 }

// POST /pagamentos (forma: pix | cartao | dinheiro | boleto; padrão pix)
{ "aluno_id": 1, "valor": 99.90, "referencia": "2026-11", "forma": "pix" }
```

### Códigos de resposta

Erros retornam no formato `{"erro": "mensagem"}`.

- 200 / 201: sucesso (201 nas criações)
- 400: JSON ausente ou campo inválido/faltando
- 404: registro não encontrado
- 422: plano inexistente, ou aluno inativo ao registrar pagamento
- 503: serviço remoto indisponível (com compensação, quando aplicável)

### Dados iniciais

- Planos: Mensal (R$ 99,90), Trimestral (R$ 269,90), Anual (R$ 899,90)
- Instrutores: Carlos Souza (Musculação), Fernanda Lima (Funcional)
- Alunos: Ana (ativa), Bruno (ativo), Camila (inativa - usada para testar a validação de pagamento)

## 3. Execução local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
```

Em quatro terminais:

```bash
cd servico_alunos      && python app.py   # 5001
cd servico_planos      && python app.py   # 5002
cd servico_instrutores && python app.py   # 5003
cd servico_pagamentos  && python app.py   # 5004
```

## 4. Demonstração (Thunder Client)

Importar `thunder-client/thunder-collection_academia.json`. A coleção contém uma pasta por serviço (CRUD) e uma pasta de integrações:

1. GET /alunos/1 retorna o aluno com o plano embutido.
2. Pagamento do aluno 3 (inativo) retorna 422.
3. Pagamento do aluno 1 retorna 201 e atualiza a situação para "em dia".
4. Com o serviço de Alunos desligado, registrar um pagamento retorna 503 sem derrubar o Pagamentos.
5. Se o Alunos cair entre a validação e a alteração, o log mostra as 3 tentativas de PATCH e a remoção do pagamento (compensação).

## 5. Publicação no Render

Criar quatro Web Services, um por pasta. Em cada um:
- Root Directory: a pasta do serviço (servico_alunos, servico_planos, servico_instrutores ou servico_pagamentos)
- Build Command: pip install -r ../requirements.txt
- Start Command: gunicorn app:app

Variáveis de ambiente (usar URLs públicas):
- servico_alunos: PLANOS_URL, INSTRUTORES_URL
- servico_pagamentos: ALUNOS_URL

O Render define PORT automaticamente. Acessar a rota `/` de cada serviço antes da demonstração para evitar a hibernação do plano gratuito.

## Estrutura

```
servico_alunos/       app.py, models.py, regras.py, rotas.py, planos_helper.py, instrutores_helper.py
servico_planos/       app.py, models.py, regras.py, rotas.py
servico_instrutores/  app.py, models.py, regras.py, rotas.py
servico_pagamentos/   app.py, models.py, regras.py, rotas.py, alunos_helper.py
thunder-client/        thunder-collection_academia.json
requirements.txt
README.md
```
