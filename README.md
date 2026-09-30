# Pesquisa de Clima

Plataforma corporativa para realização e acompanhamento de pesquisas de clima e ambiente organizacional.

O sistema será utilizado para coletar respostas confidenciais dos colaboradores, consolidar resultados por pilares, acompanhar adesão, identificar pontos de atenção e apoiar a criação de planos de ação.

## Status

Projeto em desenvolvimento.

Atualmente está concluída apenas a fundação técnica da aplicação.

Ainda não estão implementados:

- autenticação Feishu;
- autenticação externa por e-mail;
- banco de dados;
- usuários e permissões;
- pesquisas;
- pilares;
- perguntas;
- respostas;
- anonimização;
- dashboards;
- relatórios;
- planos de ação;
- inteligência artificial.

## Arquitetura

### Frontend

- React
- TypeScript
- TanStack Start
- TanStack Router
- Vite

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy
- PyMySQL
- Pydantic Settings
- Uvicorn
- Pytest

### Banco de dados

O projeto utilizará MySQL.

O banco ainda não está configurado nesta etapa.

Alterações de schema serão preparadas em arquivos SQL, revisadas e aplicadas manualmente.

## Estrutura

```text
pesquisa-clima/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   └── services/
│   ├── sql/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── docs/
├── src/
│   ├── routes/
│   ├── router.tsx
│   ├── routeTree.gen.ts
│   └── styles.css
├── package.json
├── package-lock.json
├── tsconfig.json
├── tsr.config.json
└── vite.config.ts