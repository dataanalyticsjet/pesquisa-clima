# Configuração necessária para produção

Este documento registra as configurações que devem ser fornecidas pelo ambiente de servidor antes da publicação. Nenhum domínio, segredo ou valor de produção foi definido neste repositório.

## Frontend e proxy

- Mantenha `VITE_API_BASE_URL` vazio para o navegador chamar a API pelo caminho relativo `/api` no mesmo domínio da aplicação.
- Em desenvolvimento local, `VITE_API_PROXY_TARGET` configura somente o proxy do servidor Vite para o backend local. Essa variável não é usada pelo build de produção.
- Em produção, configure o proxy reverso do servidor para encaminhar `/api` ao FastAPI. Não use `localhost` ou `127.0.0.1` em variáveis expostas ao navegador.

## Variáveis do servidor

Configure no ambiente protegido do backend, nunca no frontend nem em variáveis `VITE_`:

- `APP_ENV=production` e `APP_DEBUG=false`.
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` e `DB_PASSWORD` para a instância MySQL de produção.
- `FEISHU_OAUTH_ENABLED=true`, `FEISHU_OAUTH_APP_ID` e `FEISHU_OAUTH_APP_SECRET` para o aplicativo corporativo.
- `FEISHU_OAUTH_REDIRECT_URI` com a URL de callback registrada no Feishu.
- `FRONTEND_BASE_URL` com a origem pública da aplicação, usada no redirecionamento após autenticação.
- `SESSION_SECRET` com um valor forte e exclusivo do ambiente e `SESSION_SECURE=true` quando servido por HTTPS.
- `ALLOWED_CORPORATE_DOMAINS` com os domínios corporativos autorizados.
- `API_HOST` e `API_PORT` conforme a rede e o processo do servidor.

Se o login externo por e-mail também for habilitado, configure `EXTERNAL_EMAIL_LOGIN_ENABLED` e as variáveis `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_SSL` e `SMTP_STARTTLS` no servidor.

Use o arquivo `backend/.env.example` apenas como catálogo de nomes e padrões. Segredos reais devem ficar em um gerenciador de segredos ou configuração protegida do ambiente de produção.

## Decisões antes da publicação

- `CLIMATE_2026` está `ACTIVE` no ambiente de teste, conforme o estado informado para esta etapa. Decida o estado apropriado para a publicação; este documento não altera o banco.
- A fonte oficial da população convidada ainda não está configurada. A página de adesão deve continuar exibindo dados indisponíveis até essa fonte existir; não derive convidados da tabela de usuários.
