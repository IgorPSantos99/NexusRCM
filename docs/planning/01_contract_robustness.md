# Checklist de Implementacao - Contratos NexusRCM

Use este arquivo como lista unica de acompanhamento para a migracao dos contratos, excecoes, modelos e validacoes do projeto.

* branch `refactor/contract-robustness`

## Escopo Obrigatorio

### `exceptions.py`

- [ ] 1. Criar `src/exceptions.py` completo.
  - [ ] 1.1. Criar `NexusRCMError(Exception)` como classe base do projeto.
  - [ ] 1.2. Adicionar atributo opcional `reason: str | None` para mensagem estruturada.
  - [ ] 1.3. Criar `LoaderError(NexusRCMError)` com atributos `source: Path` e `reason: str`.
  - [ ] 1.4. Montar automaticamente a mensagem de `LoaderError`: `Failed to load '{source}': {reason}`.
  - [ ] 1.5. Criar `ExtractionError(NexusRCMError)` para falhas irrecuperaveis do pipeline NLP, como modelo nao carregado ou out of memory.
  - [ ] 1.6. Garantir que `ExtractionError` nao seja usada para input de baixa qualidade.
  - [ ] 1.7. Criar `GraphStoreError(NexusRCMError)` para falhas de operacoes no grafo, como no inexistente ou backend indisponivel.
  - [ ] 1.8. Criar `VectorStoreError(NexusRCMError)` para falhas no vector store, como dimensoes inconsistentes ou backend indisponivel.
  - [ ] 1.9. Criar `RetrievalError(NexusRCMError)` para busca completa sem evidencia relevante.
  - [ ] 1.10. Criar `IngestionError(NexusRCMError)` como erro base para ingestao.
  - [ ] 1.11. Criar `DiagnosticError(NexusRCMError)` como erro base para diagnostico.
  - [ ] 1.12. Exportar todas as excecoes no `__all__` do arquivo.

- [ ] 2. Escrever testes para as excecoes.
  - [ ] 2.1. Garantir heranca correta de todas as excecoes.
  - [ ] 2.2. Validar atributos estruturados, incluindo `reason` e `source`.
  - [ ] 2.3. Validar a mensagem automatica de `LoaderError`.
  - [ ] 2.4. Validar que as excecoes publicas estao exportadas em `__all__`.

### `interfaces.py` - Modelos Pydantic

- [ ] 3. Substituir todos os `TypedDict` por modelos `pydantic.BaseModel`.
  - [ ] 3.1. Remover dependencias de `TypedDict` nos contratos publicos.
  - [ ] 3.2. Garantir validacao runtime nos modelos migrados.
  - [ ] 3.3. Preservar os nomes publicos dos tipos existentes.

- [ ] 4. Converter `SourceRef` para `BaseModel`.
  - [ ] 4.1. Manter `filename: str`.
  - [ ] 4.2. Manter `page: int | None = None`.
  - [ ] 4.3. Manter `chunk_index: int | None = None`.

- [ ] 5. Converter `DocumentChunk` para `BaseModel`.
  - [ ] 5.1. Adicionar `default_factory=lambda: str(uuid4())` em `chunk_id`.
  - [ ] 5.2. Adicionar `field_validator` em `text` para rejeitar string vazia ou somente whitespace.
  - [ ] 5.3. Usar validacao equivalente a `Field(..., min_length=1)` quando fizer sentido.

- [ ] 6. Converter `ExtractionResult` para `BaseModel`.
  - [ ] 6.1. Usar `default_factory=list` em todos os campos `list[str]`.
  - [ ] 6.2. Garantir que resultado vazio seja valido e nao represente erro.

- [ ] 7. Converter `RetrievalResult` para `BaseModel`.
  - [ ] 7.1. Adicionar campo `strategy: RetrievalStrategy`.
  - [ ] 7.2. Adicionar campo `graph_path: GraphPath | None = None`.
  - [ ] 7.3. Preencher `graph_path` somente para resultados estruturais quando aplicavel.

- [ ] 8. Converter `DiagnosticResponse` para `BaseModel`.
  - [ ] 8.1. Adicionar `Field(ge=0.0, le=1.0)` em `confidence`.
  - [ ] 8.2. Adicionar `field_validator` em `failure_modes_identified` para rejeitar listas vazias.
  - [ ] 8.3. Adicionar `field_validator` em `recommended_actions` para rejeitar listas vazias.

- [ ] 9. Converter `GraphNode` e `GraphEdge` para `BaseModel`.
  - [ ] 9.1. Nao adicionar campos novos.
  - [ ] 9.2. Manter apenas a migracao para validacao em runtime.

- [ ] 10. Criar `GraphPath(BaseModel)`.
  - [ ] 10.1. Adicionar `nodes: list[str]`.
  - [ ] 10.2. Adicionar `edges: list[GraphEdge]`.
  - [ ] 10.3. Adicionar `total_depth: int`.
  - [ ] 10.4. Usar `GraphPath` para substituir `list[list[str]]` no retorno de `query_path`.

- [ ] 11. Criar `RetrievalStrategy(StrEnum)`.
  - [ ] 11.1. Adicionar `SEMANTIC = "semantic"`.
  - [ ] 11.2. Adicionar `STRUCTURAL = "structural"`.
  - [ ] 11.3. Adicionar `HYBRID = "hybrid"`.
  - [ ] 11.4. Usar `StrEnum` para serializacao JSON automatica.

### `interfaces.py` - Protocols

- [ ] 12. Atualizar `BaseLoader`.
  - [ ] 12.1. Adicionar atributo de classe `supported_extensions: frozenset[str]`.
  - [ ] 12.2. Adicionar atributo de classe `max_file_size_bytes: int`.
  - [ ] 12.3. Alterar retorno de `load()` de `list[DocumentChunk]` para `Iterator[DocumentChunk]` ou `Generator[DocumentChunk, None, None]`.
  - [ ] 12.4. Documentar que `load()` retorna lista ou iterador vazio quando nao ha texto extraivel.
  - [ ] 12.5. Documentar que `load()` levanta `LoaderError` para arquivo ausente, corrompido ou nao suportado.
  - [ ] 12.6. Adicionar docstring com secao `Raises: LoaderError`.

- [ ] 13. Atualizar `BaseExtractor.extract`.
  - [ ] 13.1. Documentar que input de baixa qualidade retorna listas vazias.
  - [ ] 13.2. Documentar que falha irrecuperavel levanta `ExtractionError`.
  - [ ] 13.3. Documentar idempotencia: chamadas repetidas com o mesmo chunk produzem resultado equivalente.

- [ ] 14. Atualizar `GraphStore`.
  - [ ] 14.1. Alterar `query_path` para retornar `list[GraphPath]`.
  - [ ] 14.2. Adicionar `has_node(self, node_id: str) -> bool`.
  - [ ] 14.3. Adicionar `remove_node(self, node_id: str) -> None`.
  - [ ] 14.4. Documentar que `remove_node` remove todas as arestas conectadas.
  - [ ] 14.5. Adicionar `remove_edge(self, source: str, target: str, relationship_type: str) -> None`.
  - [ ] 14.6. Mudar assinaturas do `GraphStore` para `async` quando representarem chamadas a backend.

- [ ] 15. Atualizar `BaseVectorStore`.
  - [ ] 15.1. Mudar assinaturas do `BaseVectorStore` para `async`.
  - [ ] 15.2. Documentar semantica de upsert em `add`: id existente sobrescreve embedding e metadata.
  - [ ] 15.3. Documentar que `add` levanta `VectorStoreError` se `ids` e `embeddings` tiverem comprimentos diferentes.
  - [ ] 15.4. Documentar que `query` retorna resultados ordenados por score decrescente.
  - [ ] 15.5. Documentar que `query` pode retornar menos que `top_k` se a colecao for menor.

- [ ] 16. Atualizar `DiagnosticAgent.answer`.
  - [ ] 16.1. Converter para `async def answer(self, question: str, top_k: int = 5) -> DiagnosticResponse`.
  - [ ] 16.2. Documentar que levanta `RetrievalError` se nenhuma evidencia for encontrada.
  - [ ] 16.3. Documentar que levanta `ExtractionError` se o LLM falhar em produzir output estruturado valido apos retries.

### `interfaces.py` - Modulo Publico

- [ ] 17. Adicionar `__contract_version__ = "0.1.0"`.
  - [ ] 17.1. Posicionar logo apos os imports.
  - [ ] 17.2. Alinhar com a versao semantica `v0.1.0` da Fase 1.

- [ ] 18. Atualizar imports de excecoes.
  - [ ] 18.1. Importar `LoaderError`.
  - [ ] 18.2. Importar `ExtractionError`.
  - [ ] 18.3. Importar `GraphStoreError`.
  - [ ] 18.4. Importar `VectorStoreError`.
  - [ ] 18.5. Importar `RetrievalError`.
  - [ ] 18.6. Evitar importacao circular.

- [ ] 19. Atualizar `__all__`.
  - [ ] 19.1. Incluir `GraphPath`.
  - [ ] 19.2. Incluir `RetrievalStrategy`.
  - [ ] 19.3. Incluir `__contract_version__`.
  - [ ] 19.4. Manter os nomes dos tipos migrados de `TypedDict` para `BaseModel`.
  - [ ] 19.5. Remover qualquer export obsoleto que referencie diretamente `TypedDict`.

### Verificacao

- [ ] 20. Rodar `mypy --strict`.
  - [ ] 20.1. Corrigir os erros novos que aparecerem.
  - [ ] 20.2. Registrar separadamente qualquer erro legado que nao seja corrigido nesta rodada.

- [ ] 21. Rodar `pytest`.
  - [ ] 21.1. Garantir que os testes novos passem.
  - [ ] 21.2. Garantir que os testes existentes continuem passando.
  - [ ] 21.3. Investigar regressao antes de marcar este item como concluido.

## Escopo Opcional / Portfolio

- [ ] 22. Adicionar contratos de telemetria.
  - [ ] 22.1. Criar modelo `UsageMetrics`.
  - [ ] 22.2. Adicionar contagem de tokens quando disponivel.
  - [ ] 22.3. Adicionar latencia quando disponivel.
  - [ ] 22.4. Adicionar `UsageMetrics` dentro de `DiagnosticResponse`.
  - [ ] 22.5. Incluir `UsageMetrics` em `__all__` se implementado.

- [ ] 23. Atualizar contratos do grafo para idempotencia.
  - [ ] 23.1. Avaliar troca de `add_node` por `upsert_node`.
  - [ ] 23.2. Adicionar assinatura `delete_node` se ela for diferente de `remove_node`.
  - [ ] 23.3. Marcar como TODO se a implementacao concreta ainda nao existir.

## Ordem Recomendada

1. Criar `exceptions.py` e testes das excecoes.
2. Migrar modelos `TypedDict` para Pydantic.
3. Criar `RetrievalStrategy` e `GraphPath`.
4. Atualizar `Protocols`, assincronismo e iteradores.
5. Atualizar `__contract_version__`, imports e `__all__`.
6. Executar `mypy --strict` e corrigir erros.
7. Executar `pytest` e corrigir regressoes.
8. Implementar telemetria e idempotencia do grafo, se o escopo opcional for aprovado.

## Observacoes Tecnicas

- A migracao para `async` altera consumidores e implementacoes concretas; procurar todos os usos antes de alterar as assinaturas.
- A troca de `list` por iterador em loaders pode exigir ajustes em codigo que usa `len(...)`, indexacao ou reuso do resultado.
- Validacoes Pydantic devem falhar cedo nos limites dos contratos para evitar dados invalidos no pipeline.
- Inputs de baixa qualidade devem produzir resultados vazios quando isso for comportamento esperado, nao excecoes.
- Excecoes devem representar falhas operacionais ou estados irrecuperaveis, nao ausencia normal de dados.
