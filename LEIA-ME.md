# Barbearia — back-end Django + MySQL

Este pacote contém o projeto original reorganizado e APIs JSON para o front-end. **Não inclui banco de dados, senha, venv nem backup SQL.**

## Atenção: estado de validação

As migrations 0003 e 0004 foram escritas para preservar o histórico de 0001/0002 e importar profissionais/serviços antigos. **Não foi possível executar Django/MySQL neste ambiente**. Faça primeiro um backup SQL atualizado e valide as migrations em cópia do banco, antes de aplicar ao banco principal.

## Instalação no Windows (PowerShell)

1. Extraia em uma pasta nova, sem sobrescrever o projeto original.
2. Ative o ambiente virtual existente ou crie outro (`py -m venv venv`; `.\venv\Scripts\Activate.ps1`).
3. `pip install -r requirements.txt`
4. Configure variáveis de ambiente no PowerShell (o Django não lê `.env` automaticamente):
   `$env:MYSQL_PASSWORD = 'SUA_SENHA'`
   `$env:DJANGO_SECRET_KEY = 'CHAVE_LONGA_ALEATORIA'`
5. Faça backup do MySQL, teste em cópia, depois rode:
   `python manage.py check`
   `python manage.py migrate --plan`
   `python manage.py migrate`
   `python manage.py runserver`

## Endpoints JSON

- `GET /api/csrf/` — define o cookie CSRF para o front-end
- `GET /api/servicos/` — catálogo
- `POST /api/clientes/` — cadastro com `nome`, `telefone`, `endereco`, `email`, `cpf`
- `GET /api/profissionais/?data=2026-11-02&servico_id=1&servico_id=2` — profissionais livres
- `GET /api/horarios/?data=2026-11-02&profissional_id=1&servico_id=1` — horários livres
- `POST /api/resumo/` — `{"servicos":[1,2]}`
- `POST /api/agendamentos/` — `{"cliente_id":1,"profissional_id":1,"data":"2026-11-02","horario":"09:00","servicos":[1,2]}`

POST exige token CSRF do Django quando utilizado por navegador. O front deve enviar cookie `csrftoken` e header `X-CSRFToken`; não desative CSRF. Autenticação/autorização de clientes e políticas de acesso à API ainda precisam ser definidas antes de publicar o serviço na internet. Não exponha o sistema publicamente com DEBUG ativo.

Durante o desenvolvimento, CORS e origens confiáveis de CSRF aceitam `http://localhost:4200` e `http://127.0.0.1:4200`. O Angular deve chamar `GET /api/csrf/` e enviar as requisições com credenciais (`withCredentials: true`), incluindo o valor do cookie `csrftoken` no header `X-CSRFToken`. Para outra origem, configure `CORS_ALLOWED_ORIGINS` e `CSRF_TRUSTED_ORIGINS` no ambiente do Django com as origens exatas, separadas por vírgula.

## Dados legados

A migration 0004 copia barbeiros e serviços legados para os apps dedicados, relaciona os agendamentos ao novo profissional e preserva itens contratados. **Não cria CPF/e-mail fictícios**: agendamentos antigos permanecem com `cliente_nome` e `cliente_telefone`, e `cliente` nulo até a regularização cadastral. As tabelas legadas continuam existindo por compatibilidade e para evitar perda de dados. A limpeza delas deve ser feita numa migração posterior validada.

## Limitações conhecidas

- E-mail padrão vai ao console; SMTP exige configuração.
- Horários calculados em intervalos de 15 minutos, com jornadas e bloqueios cadastrados no admin.
- Não inclui pagamento online, login de cliente, cancelamento autenticado ou testes integrados em MySQL.
- Recomenda-se trocar a senha MySQL anteriormente exposta em conversas/arquivos.
