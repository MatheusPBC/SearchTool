# Product Spec

## Frase Central

Uma IA que aprende um dominio junto com o usuario ate conseguir propor o melhor MVP possivel.

## Principio

O agente mantem quatro estados separados:

- o que sabemos;
- o que acreditamos saber;
- o que nao sabemos;
- o que precisamos descobrir para melhorar o MVP.

## Criterios de Nao Finalizacao

Uma rodada nao deve ser marcada como concluida se:

- existir pergunta critica sem resposta;
- existir hipotese sem evidencia;
- existir dependencia tecnica desconhecida;
- existir concorrente relevante nao analisado;
- `confidence_score < 85`.

## Entidades

- Project
- ResearchTopic
- Source
- Finding
- Hypothesis
- OpenQuestion
- Decision
- Entity
- Relationship

## Loop Principal

```text
while confidence < target:
  gerar_perguntas()
  pesquisar()
  extrair_conhecimento()
  criar_hipoteses()
  criticar_hipoteses()
  encontrar_lacunas()
  pesquisar_novamente()
  atualizar_mvp()
```

