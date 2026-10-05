# Proposta de schema da Pesquisa de Clima

## Estado e escopo

Este documento descreve uma proposta para revisão humana. O banco ainda não foi escolhido nem criado. Os arquivos SQL não contêm `USE` nem `CREATE DATABASE`, não são executados pela aplicação e não foram aplicados. Esta etapa não cria conexão, models ORM, repositories, services ou APIs.

O questionário de 2026 tem uma pesquisa, 13 seções e 42 perguntas. O seed é criado a partir de `src/data/mockSurvey.ts`; essa fonte não deve ser alterada para preparar o banco.

## Separação entre identidade e respostas

O domínio de identidade pode saber quem é a pessoa e se ela concluiu a pesquisa. O domínio anônimo pode saber o conteúdo e os recortes organizacionais da resposta. Não existe relacionamento de pessoa para resposta: nenhum `user_id`, e-mail, ID Feishu, `session_id` ou `participation_id` é armazenado no domínio anônimo.

```text
IDENTIDADE / PARTICIPAÇÃO
users
  │
  └── survey_participation ── surveys
          │
          X
          X SEM RELAÇÃO
          X
RESPOSTAS ANÔNIMAS
anonymous_responses ── surveys
  │
  ├── response_answers
  │      └── response_answer_options ── survey_question_options
  │
  └── anonymous_response_segments

surveys ── survey_sections ── survey_questions ── survey_question_options
```

O vínculo de cada domínio com `surveys` só informa a qual pesquisa os dados pertencem; ele não liga uma resposta a um usuário. Não criar Foreign Key ou identificador que atravesse a separação marcada com X.

## Tabelas

### Identidade e acesso — `001_identity_and_access.sql`

- **`users`**: cadastro de acesso futuro; guarda e-mail, nome, tipo, status e IDs Feishu opcionais. Datas `DATETIME` seguem UTC.
- **`roles`**: catálogo de perfis, sem atribuir perfis a usuários.
- **`user_roles`**: liga usuário e perfil, com unicidade por par.
- **`external_auth_codes`**: código de acesso externo representado somente por hash, com expiração, consumo e tentativas; não guarda OTP em texto puro.

### Definição da pesquisa — `002_survey_schema.sql`

- **`surveys`**: código único, título, textos de introdução (`intro_text`) e conclusão (`completion_text`), status, versão, período, datas de auditoria e `min_group_size` (inicial 5).
- **`survey_sections`**: código e título da seção, posição e tipo de análise (`SEGMENT`, `SCORE`, `MIXED`, `NPS`, `OPEN_TEXT`). Ordem e código são únicos dentro da pesquisa.
- **`survey_questions`**: número/código, seção, tipo de entrada, texto, texto auxiliar, placeholder, rótulos extremos opcionais para NPS, obrigatoriedade, posição, papel analítico e origem das opções. A chave estrangeira composta garante que seção e pergunta sejam da mesma pesquisa.
- **`survey_question_options`**: catálogo de opções, ordem, score opcional e indicação de opção exclusiva. Inclui uma chave única `(question_id, id)` para suportar integridade composta na junção de respostas. Likert usa score 1–5; NPS usa 0–10; categorias não têm score.

### Participação — `002_survey_schema.sql`

- **`survey_participation`**: registra que um usuário concluiu uma pesquisa. Guarda `survey_id`, `user_id`, estado `COMPLETED` e `completed_on DATE NOT NULL`. Não guarda resposta nem horário preciso. Nesta versão não há estado `IN_PROGRESS`: rascunhos não são persistidos e uma linha representa uma conclusão.

### Conteúdo anônimo — `002_survey_schema.sql`

- **`anonymous_responses`**: contém somente `response_id` aleatório (UUID em `CHAR(36)` ASCII/binário) e `survey_id`. Não tem timestamp de envio, identidade, IP, sessão ou agente de usuário.
- **`response_answers`**: guarda `response_id`, `survey_id`, `question_id` e `text_value`; não tem `numeric_value`. `SELECT` organizacional grava em `text_value` o código validado. `TEXTAREA` e `SHORT_TEXT` gravam o texto ali. Há no máximo uma resposta por pergunta em cada resposta. FKs compostas exigem que a resposta anônima e a pergunta pertençam à mesma pesquisa.
- **`response_answer_options`**: associa uma resposta a uma ou mais opções para escolha única/múltipla, Likert ou NPS. Guarda também `question_id`; FKs compostas garantem que a opção pertence à mesma pergunta da resposta. A validação de quantidade/tipo de opções ocorre no backend futuro. Valores de score Likert/NPS vêm de `survey_question_options.score_value`.
- **`anonymous_response_segments`**: guarda somente `response_id`, tipo e código do recorte para análise agregada. Não tem campos de usuário.

As FKs compostas garantem que `(response_id, survey_id)` de uma resposta pertença a `anonymous_responses`, que `(survey_id, question_id)` pertença a `survey_questions`, que `(answer_id, question_id)` pertença à resposta correta e que `(question_id, option_id)` pertença à pergunta correta. Assim, uma resposta não pode conter uma pergunta de outra pesquisa nem uma opção de outra pergunta. As chaves referenciadas são suportadas pelas UNIQUEs `(response_id, survey_id)`, `(survey_id, id)`, `(id, question_id)` e `(question_id, id)`, respectivamente.

## Regra de uma participação

`UNIQUE (survey_id, user_id)` em `survey_participation` é a barreira final do banco contra duas conclusões da mesma pesquisa pelo mesmo usuário, inclusive em duas abas ou requisições simultâneas. O backend futuro deve executar a persistência da resposta anônima e da participação concluída em uma transação. Se a constraint for violada, toda a transação perdedora deve sofrer rollback e a API responder `409 Conflict` / `SURVEY_ALREADY_COMPLETED`.

A atomicidade não requer FK entre os domínios. A submissão primeiro valida a pesquisa e a elegibilidade, salva resposta/itens, insere a participação e confirma tudo junto; qualquer falha reverte todas as gravações.

## Opções de operação e perfil de atuação

Q1 e Q2 usam `option_source` `ORG_REGIONAL` e `ORG_BASE`; o seed não inclui opções organizacionais demonstrativas. O backend fornece as Regionais e unidades válidas a partir do catálogo aprovado. As seleções validadas são persistidas em `response_answers.text_value` e alimentam somente os segmentos anônimos `REGIONAL` e `BASE`.

Q3 é uma pergunta obrigatória `SINGLE_CHOICE`, com `option_source` `STATIC` e opções `OPERATIONAL` / “Operacional” e `ADMINISTRATIVE` / “Administrativo”. É uma categoria de perfil e não gera segmento organizacional. A aplicação mantém opções antigas de Q3 fora da definição atual; respostas anônimas históricas e os valores legados de CNPJ no schema são preservados para compatibilidade, sem criar novas respostas ou segmentos CNPJ.

Área não é uma pergunta do formulário oficial e não foi adicionada às perguntas. A segmentação prevê `AREA`, mas o comentário no SQL registra que sua fonte só será definida antes da implementação do backend; não inferir nem preencher esse recorte até aprovação formal.

## Anonimato, tempo e logs

O objetivo é anonimato no nível da aplicação e do banco, sem alegar anonimato criptográfico absoluto. `survey_participation` tem a identidade e `anonymous_responses` tem o conteúdo, sem FK ou identificador compartilhado entre eles. A resposta não armazena data/hora; a participação pode guardar apenas a data UTC de conclusão, sem horário preciso. As demais datas `DATETIME` do backend devem ser escritas e interpretadas em UTC.

Nunca colocar no mesmo evento/log `user_id` e `response_id`, e-mail e `response_id`, ou ID Feishu e `response_id`. Não registrar respostas abertas, conteúdo integral respondido, tokens de sessão, OTP ou `access_token`. A API não deve expor identificadores/metadados que facilitem correlação.

## Proteção de grupos pequenos

Toda consulta gerencial segmentada exige:

```sql
COUNT(DISTINCT response_id) >= surveys.min_group_size
```

O valor inicial é 5. Exemplo: Regional SPS + Área Operações + Base X com três respostas não deve aparecer. O limite se aplica à combinação completa de filtros e a qualquer drill-down; nenhuma contagem auxiliar pode permitir inferência de respostas individuais. Esta etapa documenta a regra, sem criar views analíticas.

## Arquivos SQL

1. `backend/sql/001_identity_and_access.sql` — tabelas de identidade e acesso.
2. `backend/sql/002_survey_schema.sql` — pesquisas, perguntas, participação e respostas anônimas.
3. `backend/sql/003_seed_climate_survey_2026.sql` — uma pesquisa em estado `DRAFT`, 13 seções, 42 perguntas e opções estáticas oficiais.

Todos são InnoDB com `utf8mb4` / `utf8mb4_unicode_ci`, não escolhem nome de database e aguardam revisão humana antes de qualquer aplicação.
