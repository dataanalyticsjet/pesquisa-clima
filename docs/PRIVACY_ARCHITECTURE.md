# Arquitetura de privacidade e identidade

## Escopo desta etapa

Esta etapa define a proposta dos domínios de identidade/participação e pesquisa/respostas anônimas por meio de documentação e arquivos SQL para revisão manual. A aplicação não executa esses arquivos automaticamente e nenhum banco foi selecionado ou conectado.

O arquivo SQL não escolhe um schema. O nome oficial do banco ainda precisa ser definido; a pessoa responsável deve selecionar o schema explicitamente no cliente SQL antes de qualquer aplicação manual.

## Domínio de identidade

Estas tabelas sabem quem é o usuário:

- **users**: e-mail, nome, tipo de acesso, status, identificadores opcionais do Feishu e datas de atividade.
- **roles**: catálogo dos quatro perfis iniciais.
- **user_roles**: associação normalizada entre usuário e perfil.
- **external_auth_codes**: e-mail de destino e somente o hash do código, junto com expiração, uso e tentativas.

Relações propostas:

- Um usuário pode ter vários perfis; um perfil pode pertencer a vários usuários.
- A combinação de user_id e role_id é única em user_roles.
- external_auth_codes não possui user_id nem chave estrangeira para users. O endereço é usado para o fluxo futuro de acesso externo.
- Os IDs Feishu são opcionais e únicos quando presentes. Acesso externo não depende deles.
- Não são armazenados senha, OTP em texto puro ou tokens/segredos Feishu.

### Tipos de acesso e perfis

- **INTERNAL** identifica acesso que futuramente usará o provedor Feishu.
- **EXTERNAL** identifica acesso que futuramente usará e-mail e OTP.
- **COLLABORATOR** participa de pesquisas liberadas.
- **MANAGEMENT** consulta resultados e acompanhamento autorizado.
- **SURVEY_ADMIN** administra pesquisas, pilares, perguntas e acompanhamento.
- **ADMIN** administra tecnicamente a plataforma e os acessos.

A tabela roles contém apenas definições de perfil; ela não atribui perfis a usuários. A criação futura de usuários deve começar sem privilégios elevados. Qualquer atribuição automática deve ser restrita ao perfil COLLABORATOR; MANAGEMENT, SURVEY_ADMIN e ADMIN exigem concessão explícita e autorizada. O status inicial proposto é INACTIVE para exigir ativação explícita.

## Domínio anônimo de respostas proposto

O schema deste domínio está descrito em `backend/sql/002_survey_schema.sql`, mas o arquivo não foi executado e nenhuma tabela foi criada:

- **anonymous_responses**: representará uma resposta anônima a uma pesquisa.
- **response_answers**: representará as respostas individuais pertencentes a uma resposta anônima.

Essas tabelas saberão o que foi respondido, mas não a identidade de quem respondeu. Não haverá Foreign Key entre usuário/participação e resposta anônima. Não devem existir colunas ou chaves de correlação como user_id, email, feishu_open_id, feishu_union_id ou participation_id em `anonymous_responses`, `response_answers` ou segmentos anônimos.

Os domínios também não devem compartilhar um identificador que permita reconstruir essa ligação. Campos de tempo, escopo ou metadados futuros precisam passar por revisão de privacidade para evitar reidentificação indireta. A separação entre identidade e conteúdo respondido deve ser preservada em banco, API, logs e relatórios.

## Decisões de implementação adiadas

Esta etapa não implementa Feishu OAuth, callback, envio de e-mail, OTP real, sessões, JWT, cookies, endpoints de login ou persistência operacional de respostas. Os arquivos SQL contêm apenas proposta de DDL e seed para revisão, sem execução. O armazenamento futuro de OTP deverá conter somente um hash seguro; como códigos OTP têm baixa entropia, a implementação deve avaliar uma construção com chave mantida fora do banco, sem gravar APP_SECRET ou tokens em tabela.

O backend atual ainda não possui Base declarativa, fábrica de sessões ou configuração de persistência SQLAlchemy. Por isso, modelos ORM não foram adicionados nesta etapa: a proposta permanece no SQL para revisão e não cria fundação de conexão ou dependência operacional com banco.

## Proteção contra correlação indireta

A proposta separa o registro de participação do conteúdo da pesquisa:

- `survey_participation` sabe qual usuário concluiu uma pesquisa.
- `anonymous_responses` sabe a qual pesquisa pertence o conteúdo respondido.
- Não existe Foreign Key, `user_id`, `participation_id`, e-mail, identificador Feishu ou identificador compartilhado entre esses registros.
- `anonymous_responses` não armazena horário nem data de envio.
- `survey_participation` não armazena horário preciso de conclusão; `completed_on` é, no máximo, uma data.

O objetivo é anonimato em nível de aplicação e banco, reduzindo ligações diretas e oportunidades de correlação. Isso não é uma afirmação de anonimato criptográfico absoluto: acesso administrativo, combinação com dados externos ou recortes pequenos ainda podem criar riscos e precisam de controles próprios.

### Regras para logs e API futuros

Nunca registrar no mesmo log ou evento `user_id` junto de `response_id`, e-mail junto de `response_id`, ou `feishu_open_id` junto de `response_id`. Logs não devem conter respostas abertas, o conteúdo completo de um questionário respondido, token de sessão, OTP ou `access_token`. Logs operacionais devem usar códigos de evento não correlacionáveis e evitar conteúdo de resposta.

A API não deve devolver simultaneamente identificadores de identidade e de resposta, nem expor identificadores, ordenação ou metadados que facilitem ligar uma participação a uma resposta. `response_id` não deve ser enviado de volta ao domínio de identidade depois da submissão.

### Tempo e fuso horário

Datas e colunas `DATETIME` do backend devem ser escritas e interpretadas em UTC, com a sessão da aplicação configurada para UTC. A resposta anônima não recebe data de envio. A participação guarda somente `completed_on DATE`, se a data for necessária, sem hora/minuto/segundo.

### Submissão futura e concorrência

O fluxo futuro é conceitual: autenticar o usuário; conferir pesquisa aberta e participação; validar perguntas obrigatórias e tipos/opções; gerar `response_id` aleatório; salvar a resposta e seus itens; registrar a participação como concluída; confirmar a transação. Todas as gravações devem ocorrer na mesma transação: se qualquer etapa falhar, tudo deve ser revertido. Mesmo dentro dessa transação, não se cria vínculo ou Foreign Key entre os domínios de participação e resposta.

A constraint `UNIQUE (survey_id, user_id)` em `survey_participation` arbitra disputas entre duplo clique, múltiplas abas, requisições simultâneas e tentativas diretas. O backend deverá reverter a resposta anônima da transação perdedora e tratar a violação como HTTP `409 Conflict`, código `SURVEY_ALREADY_COMPLETED`.

### Confidencialidade dos resultados

Toda consulta gerencial segmentada deverá exigir `COUNT(DISTINCT response_id) >= surveys.min_group_size` para o recorte completo selecionado. Com o valor inicial 5, um recorte com três respostas não é exibido. A regra também vale para combinações Regional + Área + Base + CNPJ; não se deve oferecer drill-down ou contagens auxiliares que permitam deduzir respostas individuais.

## Estado dos arquivos SQL desta etapa

`backend/sql/001_identity_and_access.sql`, `backend/sql/002_survey_schema.sql` e `backend/sql/003_seed_climate_survey_2026.sql` são artefatos para revisão humana. Não foram executados, não selecionam/criam database e não estão conectados a uma rotina de inicialização da aplicação.
