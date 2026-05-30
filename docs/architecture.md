# Architecture

## Componentes

### Research Planner

Decide quais topicos precisam ser pesquisados com base na ideia inicial, nas lacunas e no impacto sobre o MVP.

### Source Finder

Encontra documentacao, repositorios, artigos, papers, videos, foruns e concorrentes.

### Knowledge Extractor

Transforma fontes em fatos, entidades e relacoes.

### Critic

Tenta invalidar conclusoes e reduz confianca quando faltam evidencias, existem vieses ou fontes fracas.

### Domain Mapper

Conecta entidades e relacoes em um mapa causal do dominio.

### MVP Builder

Transforma conhecimento acumulado em arquitetura, MVP recomendado e backlog.

## Persistencia Planejada

PostgreSQL guarda entidades canonicas e auditoria. pgvector guarda embeddings para recuperacao semantica.

O grafo de conhecimento pode comecar em tabelas relacionais:

- `entities`
- `relationships`
- `findings`
- `sources`
- `hypotheses`

Se a exploracao de grafo ficar central ao produto, avaliar Neo4j ou AGE no PostgreSQL.

## Execucao Assincrona

Celery executa pesquisas longas:

- descoberta de fontes;
- crawlers;
- extracao;
- reavaliacao de hipoteses;
- recalculo de confianca.

