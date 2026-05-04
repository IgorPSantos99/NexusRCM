# Checklist de Implementacao - CSV Loader (SAP PM)

Use este arquivo como lista unica de acompanhamento para implementar o
`CSVLoader`, segundo componente concreto da camada de ingestao. O loader
materializa o contrato `BaseLoader` definido em `src/nexusrcm/interfaces.py`
([interfaces.py](../../src/nexusrcm/interfaces.py)) e absorve os work
orders do SAP PM (Plant Maintenance), que sao a principal fonte estruturada
de conhecimento de falha em plantas industriais.

* branch sugerida: `feat/csv-loader`
* fase do roadmap: Fase 1 - Semanas 1 e 2 (Data Pipeline)
* dependencias ja existentes: `pandas>=2.2,<3.0`, `pydantic>=2.7,<3.0`
* contrato a respeitar: `BaseLoader` Protocol em
  [interfaces.py:142](../../src/nexusrcm/interfaces.py#L142)
* excecao a propagar: `LoaderError` em
  [exceptions.py](../../src/nexusrcm/exceptions.py)
* depende de: `02_pdf_loader.md` (reusa `Settings`, `conftest.py`,
  `_validation.py` e padroes de tratamento de erro estabelecidos pelo
  `PDFLoader`)

> **Por que SAP PM como cidadao de primeira classe?** SAP PM e o sistema
> de gestao de manutencao usado em ~70% das plantas industriais do mundo.
> Ter o loader nativo para esse formato e o que diferencia o NexusRCM de
> um RAG generico: a ontologia da Secao 6 do AGENT.md (Equipment, Symptom,
> FailureMode, RootCause, CorrectiveAction) mapeia diretamente em colunas
> de SAP PM. O CSVLoader e a ponte entre o conhecimento tacito ja
> estruturado e o grafo de conhecimento.

---

## Escopo Obrigatorio

### Configuracao e Settings

- [ ] 1. Estender `src/nexusrcm/config.py` (criado em `02_pdf_loader.md`).
  - [ ] 1.1. Adicionar `csv_max_file_size_bytes: int = 100 * 1024 * 1024` (100 MB).
        CSVs sao mais densos que PDFs por byte; permitir limite maior.
  - [ ] 1.2. Adicionar `csv_default_encoding: str = "utf-8"`.
  - [ ] 1.3. Adicionar `csv_fallback_encodings: tuple[str, ...] = ("latin-1", "cp1252")`.
        Exports de SAP frequentemente vem em `cp1252` ou `latin-1`.
  - [ ] 1.4. Adicionar `csv_chunksize_rows: int = 1000` para leitura em lote (pandas).
  - [ ] 1.5. NAO adicionar `csv_chunk_size_tokens` aqui: cada linha de CSV vira UM `DocumentChunk`,
        diferente do PDF que precisa fatiar texto contiguo.

> **Por que uma linha = um chunk?** Cada work order do SAP PM e um evento
> de falha autocontido. Fragmentar uma linha quebraria a coerencia
> semantica do registro. Esta decisao deve ser registrada na ADR-004
> (rationale de dados sinteticos e formato).

### Schema das colunas SAP PM

- [ ] 2. Criar `src/nexusrcm/ingestion/sap_pm_schema.py` com o schema declarativo.
  - [ ] 2.1. Definir `class SapPmColumn(StrEnum)` com nomes canonicos das colunas.
  - [ ] 2.2. Incluir colunas obrigatorias minimas:
    - `ORDER_NUMBER = "order_number"` (chave do work order).
    - `EQUIPMENT_ID = "equipment_id"` (codigo do ativo, ex: P-101A).
    - `DESCRIPTION = "description"` (texto livre da observacao).
  - [ ] 2.3. Incluir colunas opcionais mapeadas para a ontologia:
    - `EQUIPMENT_TYPE = "equipment_type"`.
    - `MANUFACTURER = "manufacturer"`.
    - `FUNCTIONAL_LOCATION = "functional_location"`.
    - `SYMPTOM = "symptom"`.
    - `FAILURE_MODE = "failure_mode"`.
    - `ROOT_CAUSE = "root_cause"`.
    - `CORRECTIVE_ACTION = "corrective_action"`.
    - `REPORTED_AT = "reported_at"` (data ISO 8601).
    - `DURATION_HOURS = "duration_hours"`.
  - [ ] 2.4. Definir `REQUIRED_COLUMNS: frozenset[str]` com as obrigatorias.
  - [ ] 2.5. Definir `ONTOLOGY_COLUMNS: frozenset[str]` com as opcionais que viram metadados estruturados.
  - [ ] 2.6. Documentar no docstring do modulo o mapeamento coluna -> no de grafo da Secao 6.

> **Por que schema declarativo separado?** A ontologia evolui (Fase 2
> adiciona `CriticalComponent`). Manter o mapeamento em um arquivo isolado
> permite que o `CSVLoader`, o `entity_extractor` e o `graph/builder.py`
> compartilhem o mesmo vocabulario sem acoplamento.

### Estrutura do modulo

Estrutura alvo da camada de ingestao apos PDF e CSV:

```text
src/nexusrcm/ingestion/
├── __init__.py
├── _validation.py
├── pdf_loader.py
├── csv_loader.py
└── sap_pm_schema.py
```

`csv_loader.py` deve conter apenas a logica tabular/SAP PM. Validacoes
comuns de arquivo ficam em `_validation.py`; vocabulario de colunas fica em
`sap_pm_schema.py`. Essa separacao evita que mudancas no formato SAP PM
afetem o loader de PDF e evita duplicacao de guardas basicas entre loaders.

- [ ] 3. Criar `src/nexusrcm/ingestion/csv_loader.py`.
  - [ ] 3.1. Definir docstring de modulo com exemplo de CSV SAP PM minimo.
  - [ ] 3.2. Importar `pandas as pd`.
  - [ ] 3.3. Importar `BaseLoader`, `DocumentChunk`, `SourceRef` de `nexusrcm.interfaces`.
  - [ ] 3.4. Importar `LoaderError` de `nexusrcm.exceptions`.
  - [ ] 3.5. Importar `SapPmColumn`, `REQUIRED_COLUMNS`, `ONTOLOGY_COLUMNS` de `sap_pm_schema`.
  - [ ] 3.6. Importar helpers privados de `_validation.py` para tipo, existencia, extensao e tamanho.
  - [ ] 3.7. Importar `logging` e instanciar `logger = logging.getLogger(__name__)`.
  - [ ] 3.8. Adicionar `__all__ = ["CSVLoader"]`.

- [ ] 4. Atualizar `src/nexusrcm/ingestion/__init__.py`.
  - [ ] 4.1. Reexportar `CSVLoader` no `__all__` do pacote.
  - [ ] 4.2. Manter ordem alfabetica.

### Classe `CSVLoader`

- [ ] 5. Definir atributos de classe exigidos pelo Protocol.
  - [ ] 5.1. `supported_extensions: frozenset[str] = frozenset({".csv"})`.
  - [ ] 5.2. `max_file_size_bytes: int = 100 * 1024 * 1024` como default estavel de classe para introspeccao antes de instanciar.
  - [ ] 5.3. NAO incluir `.tsv` neste loader; criar TSVLoader separado se necessario.
        Heuristica de delimitador silenciosa esconde bugs.
  - [ ] 5.4. Definir `DEFAULT_CSV_MAX_FILE_SIZE_BYTES` no modulo ou em `config.py` para evitar magic number duplicado.

- [ ] 6. Implementar `__init__` configuravel.
  - [ ] 6.1. Aceitar `column_mapping: dict[str, str] | None = None`.
        Permite que clientes apontem `"Auftrag"` (alemao SAP) para `order_number`.
  - [ ] 6.2. Aceitar `required_columns: frozenset[str] | None = None` para customizar
        validacao alem do default.
  - [ ] 6.3. Aceitar `delimiter: str = ","`.
  - [ ] 6.4. Persistir os atributos privados e resolver defaults via `get_settings()`.
  - [ ] 6.5. Resolver `self.max_file_size_bytes` a partir de `Settings.csv_max_file_size_bytes` na instancia, sem alterar o default de classe.

- [ ] 7. Implementar `load(self, source: Path) -> Iterator[DocumentChunk]` como generator.
  - [ ] 7.1. Reutilizar `_validation.py` para validar tipo, existencia, extensao e tamanho do arquivo.
  - [ ] 7.2. Detectar encoding via tentativa em cascata: `utf-8` -> fallbacks da `Settings`.
        Capturar `UnicodeDecodeError` e tentar a proxima encoding.
        Se todas falharem, `LoaderError` com `reason="unable to decode with encodings <lista>"`.
  - [ ] 7.3. Ler com `pd.read_csv(source, encoding=enc, dtype=str, keep_default_na=False, chunksize=settings.csv_chunksize_rows)`.
        - `dtype=str` evita coercao indesejada (ex: `"P-101"` virando NaN).
        - `keep_default_na=False` preserva strings vazias literais como `""`.
        - `chunksize` retorna iterador de DataFrames; mantem footprint de memoria estavel.
  - [ ] 7.4. Capturar `pd.errors.EmptyDataError`, `pd.errors.ParserError` e converter em `LoaderError`.
  - [ ] 7.5. Aplicar `column_mapping` (rename) no primeiro DataFrame; assumir que os DataFrames
        seguintes terao as mesmas colunas.
  - [ ] 7.6. Validar presenca de `required_columns`; se faltar, `LoaderError` com lista de faltantes.
  - [ ] 7.7. Iterar linhas com `for row_index, row in enumerate(df.itertuples(index=False), start=offset)`,
        mantendo `offset` global atraves dos chunks de pandas para que `chunk_index` reflita a linha real do arquivo.
  - [ ] 7.8. Para cada linha, montar texto narrativo via helper `_row_to_text(row)`.
  - [ ] 7.9. Pular linhas com texto vazio apos normalizacao (logar `logger.warning` com numero da linha).
  - [ ] 7.10. Construir `SourceRef(filename=source.name, page=None, chunk_index=row_index)`.
        - `page=None` porque CSV nao tem paginas. Uso correto do contrato.
        - `chunk_index` carrega o numero da linha (1-indexed para humanos).
  - [ ] 7.11. `yield DocumentChunk(text=text, source_ref=ref, metadata=structured_metadata)`.
  - [ ] 7.12. Encerrar generator silenciosamente quando o CSV for valido mas todas as linhas estiverem vazias.

> **Por que `dtype=str`?** Pandas tenta inferir tipos por coluna. Numeros
> de ordem como `"00045"` viram `45` (perde zero a esquerda); colunas
> mistas viram `object` com NaN intercalado. Para ingestao textual,
> tratar tudo como string elimina classes inteiras de bug.
>
> **Por que reutilizar `_validation.py`?** Tipo, existencia, extensao e
> tamanho nao sao regras especificas de CSV. Reusar a mesma validacao do
> PDFLoader mantem mensagens de erro consistentes e reduz manutencao.

### Conversao linha -> texto narrativo

- [ ] 8. Implementar helper `_row_to_text(row: NamedTuple) -> str`.
  - [ ] 8.1. Renderizar template human-readable e embedding-friendly:
        `"Equipment {equipment_id}: {description}. Symptom: {symptom}. Failure mode: {failure_mode}. Root cause: {root_cause}. Corrective action: {corrective_action}."`.
  - [ ] 8.2. Omitir frases para campos vazios (nao gerar `"Symptom: ."`).
  - [ ] 8.3. Garantir que o texto final tenha pelo menos a `description`; senao retornar `""`.
  - [ ] 8.4. Preservar acentos e caracteres especiais do texto original.

- [ ] 9. Implementar helper `_row_to_metadata(row: NamedTuple) -> dict[str, Any]`.
  - [ ] 9.1. Incluir `loader: "csv"` e `format: "sap_pm"`.
  - [ ] 9.2. Incluir cada coluna de `ONTOLOGY_COLUMNS` presente na linha como chave -> valor.
  - [ ] 9.3. Excluir campos vazios para nao poluir o metadata downstream.
  - [ ] 9.4. Serializar datas para ISO 8601 string (validar se ja vier neste formato).
  - [ ] 9.5. NAO incluir `description` no metadata (ja esta no `text`); evitar duplicacao.

> **Por que separar `text` de `metadata` mesmo tendo a mesma origem?** O
> embedding usa `text` para vetorizacao semantica. O grafo usa `metadata`
> para criar nos tipados (`Equipment`, `FailureMode`). Sao consumidores
> diferentes; manter a estrutura preserva ambas as facets.

### Tratamento de erros e logs

- [ ] 10. Mapear todas as falhas operacionais para `LoaderError`.
  - [ ] 10.1. Arquivo inexistente -> `reason="file not found"`.
  - [ ] 10.2. Extensao nao suportada -> `reason="unsupported extension '<ext>'"`.
  - [ ] 10.3. Arquivo acima do limite -> `reason="file size <N> bytes exceeds limit <M>"`.
  - [ ] 10.4. CSV vazio (sem header) -> `reason="csv is empty"`.
  - [ ] 10.5. Header presente mas sem colunas obrigatorias -> `reason="missing required columns: <a>, <b>"`.
  - [ ] 10.6. Falha de parser -> `reason="malformed csv: <pandas msg>"`.
  - [ ] 10.7. Encoding indecodificavel -> `reason="unable to decode with encodings <lista>"`.
  - [ ] 10.8. Garantir que NENHUMA excecao crua de pandas ou de codecs escape do `load()`.

- [ ] 11. Adicionar logs estruturados nos pontos chave.
  - [ ] 11.1. `logger.info` ao iniciar load com filename, encoding detectado e numero de colunas.
  - [ ] 11.2. `logger.warning` para cada linha vazia descartada com numero da linha.
  - [ ] 11.3. `logger.warning` quando uma coluna opcional do `ONTOLOGY_COLUMNS` aparece com nome canonico mas tipo divergente.
  - [ ] 11.4. `logger.info` no final com numero total de chunks emitidos e numero de linhas pulada.
  - [ ] 11.5. NAO logar conteudo de `description` ou `root_cause` (privacidade industrial).

### Testes (TDD - escrever antes da implementacao)

- [ ] 12. Criar `tests/fixtures/sap_pm/` com CSVs versionados.
  - [ ] 12.1. `valid_minimal.csv` - 3 linhas com apenas as colunas obrigatorias.
  - [ ] 12.2. `valid_full_ontology.csv` - 5 linhas com todas as colunas mapeadas.
  - [ ] 12.3. `missing_required_column.csv` - falta `equipment_id`.
  - [ ] 12.4. `latin1_encoded.csv` - caracteres acentuados em `latin-1` (forcar fallback).
  - [ ] 12.5. `cp1252_encoded.csv` - exportacao tipica do SAP em Windows.
  - [ ] 12.6. `malformed.csv` - virgula extra em linha do meio.
  - [ ] 12.7. `empty.csv` - 0 bytes.
  - [ ] 12.8. `header_only.csv` - apenas cabecalho, sem linhas.
  - [ ] 12.9. `with_blank_rows.csv` - linhas com `description` vazia intercaladas.
  - [ ] 12.10. `german_columns.csv` - colunas em alemao (`Auftrag`, `Equipment`, `Beschreibung`) para testar `column_mapping`.

- [ ] 13. Criar `tests/test_csv_loader.py` com cobertura por cenario.
  - [ ] 13.1. `test_supported_extensions_contains_csv` - sanity check do contrato.
  - [ ] 13.2. `test_load_returns_iterator_not_list` - validar que retorno e generator.
  - [ ] 13.3. `test_load_happy_path_yields_chunk_per_row` - 3 linhas validas geram 3 chunks.
  - [ ] 13.4. `test_load_chunk_index_matches_row_number` - 1-indexed, considerando header.
  - [ ] 13.5. `test_load_source_ref_page_is_none` - garantir que pagina nao e usada incorretamente.
  - [ ] 13.6. `test_load_metadata_contains_ontology_columns` - validar que `failure_mode`, etc. estao em `metadata`.
  - [ ] 13.7. `test_load_text_renders_template_for_full_ontology`.
  - [ ] 13.8. `test_load_text_omits_empty_fields` - sem `"Symptom: ."`.
  - [ ] 13.9. `test_load_skips_blank_description_rows_with_warning` - usar `caplog`.
  - [ ] 13.10. `test_load_missing_required_column_raises_loader_error` - validar `exc.reason` lista as faltantes.
  - [ ] 13.11. `test_load_empty_file_raises_loader_error`.
  - [ ] 13.12. `test_load_header_only_returns_empty_iterator` - nao e erro.
  - [ ] 13.13. `test_load_malformed_csv_raises_loader_error`.
  - [ ] 13.14. `test_load_encoding_fallback_to_latin1` - usar `latin1_encoded.csv`.
  - [ ] 13.15. `test_load_encoding_fallback_to_cp1252`.
  - [ ] 13.16. `test_load_undecodable_file_raises_loader_error` - bytes invalidos em todas as encodings.
  - [ ] 13.17. `test_load_oversized_file_raises_loader_error`.
  - [ ] 13.18. `test_load_unsupported_extension_raises_loader_error`.
  - [ ] 13.19. `test_load_column_mapping_translates_german_columns`.
  - [ ] 13.20. `test_load_preserves_leading_zeros_in_order_number` - regressao do `dtype=str`.
  - [ ] 13.21. `test_load_does_not_leak_pandas_exceptions`.
  - [ ] 13.22. `test_load_is_lazy` - consumir um chunk, verificar que generator nao esgotou.
  - [ ] 13.23. `test_load_case_insensitive_extension`.

- [ ] 14. Adicionar fixtures compartilhadas em `tests/conftest.py`.
  - [ ] 14.1. `sap_pm_csv_factory(rows: list[dict]) -> Path` para gerar CSVs ad-hoc em `tmp_path`.
  - [ ] 14.2. `sap_pm_columns` retornando lista canonica para reuso.
  - [ ] 14.3. Reutilizar em `test_csv_loader.py` e em `test_pipeline_integration.py` (futuro).

### Verificacao

- [ ] 15. Rodar `ruff format` e `ruff check src tests`.
  - [ ] 15.1. Corrigir todas as ofensas (`E`, `F`, `I`, `B`, `UP`).
  - [ ] 15.2. Validar imports ordenados (stdlib -> pandas -> nexusrcm).

- [ ] 16. Rodar `mypy --strict src/nexusrcm/ingestion/csv_loader.py`.
  - [ ] 16.1. Anotar tipos completos; pandas tem stubs (`pandas-stubs`) opcionais
        - se necessario, adicionar como dev dependency ou usar `# type: ignore[...]` localizado.
  - [ ] 16.2. Garantir que `_row_to_text` e `_row_to_metadata` tem assinaturas precisas.

- [ ] 17. Rodar `pytest --cov=src/nexusrcm/ingestion/csv_loader`.
  - [ ] 17.1. Atingir cobertura >= 90% no modulo.
  - [ ] 17.2. Garantir que CI continua verde (sem regressao em outros testes).

- [ ] 18. Validar conformidade com o Protocol em runtime.
  - [ ] 18.1. Adicionar `assert isinstance(CSVLoader(), BaseLoader)` em teste dedicado.
  - [ ] 18.2. Validar `isinstance` tambem com `column_mapping` customizado.

---

## Escopo Opcional / Portfolio

- [ ] 19. Sniffer automatico de delimitador.
  - [ ] 19.1. Detectar `,` vs `;` vs `\t` via `csv.Sniffer` sobre os primeiros 4KB.
  - [ ] 19.2. Permitir override explicito via `__init__`.
  - [ ] 19.3. Logar delimitador detectado em `INFO`.

- [ ] 20. Suporte a multilinha em campos com quebra de linha.
  - [ ] 20.1. Validar que `description` com `\n` e preservada.
  - [ ] 20.2. Adicionar fixture especifica e teste.

- [ ] 21. Validacao opcional de tipos por coluna (Pandera).
  - [ ] 21.1. Avaliar Pandera vs validacao manual.
  - [ ] 21.2. NAO implementar nesta fase; criar issue `enhancement`.
  - [ ] 21.3. Trade-off documentado: dependencia adicional vs validacao declarativa.

- [ ] 22. Particionamento por work order.
  - [ ] 22.1. Avaliar se chunks podem agrupar work orders relacionados (mesmo equipment_id).
  - [ ] 22.2. Provavelmente fica para Fase 2 (ja na construcao do grafo).

- [ ] 23. Gerador de dados sinteticos.
  - [ ] 23.1. Criar `data/synthetic/generate_work_orders.py` (item separado no roadmap, Semana 1-2).
  - [ ] 23.2. Reutilizar `sap_pm_schema.py` como fonte de verdade.
  - [ ] 23.3. Documentar em ADR-004 (rastreado no AGENT.md).

---

## Ordem Recomendada

1. Estender `Settings` com parametros de CSV.
2. Criar `sap_pm_schema.py` com colunas canonicas e mapeamento de ontologia.
3. Confirmar que `_validation.py` do PDFLoader cobre as guardas comuns necessarias ao CSV.
4. Criar fixtures de CSV em `tests/fixtures/sap_pm/`.
5. Adicionar helpers em `tests/conftest.py` (factory de CSVs).
6. Escrever `tests/test_csv_loader.py` (TDD - todos falhando primeiro).
7. Implementar `CSVLoader` minimo ate o caminho feliz passar.
8. Implementar deteccao de encoding e fallbacks.
9. Implementar tratamento de erros e logs ate cobrir todos os cenarios negativos.
10. Implementar `_row_to_text` e `_row_to_metadata` em iteracoes pequenas.
11. Implementar suporte a `column_mapping`.
12. Rodar `ruff`, `mypy --strict`, `pytest --cov`.
13. Atualizar `ingestion/__init__.py` e validar `isinstance(CSVLoader(), BaseLoader)`.
13. Comitar em ordem TDD: `test(ingestion): ...` antes de `feat(ingestion): ...`.

---

## Observacoes Tecnicas

- `pandas.read_csv` com `chunksize` retorna `TextFileReader`, que e iterador
  de DataFrames. Isso permite streaming sem carregar 100 MB na RAM, mas exige
  cuidado com colunas que so aparecem em chunks posteriores - assumimos
  schema fixo, validado no primeiro chunk.
- Exports do SAP costumam ter BOM (`﻿`) no inicio. `pandas` lida
  automaticamente com `encoding="utf-8-sig"` se necessario; documente se a
  primeira encoding tentada for `"utf-8-sig"` para nao surpreender.
- O contrato `BaseLoader` exige `Iterator[DocumentChunk]`. Nao retorne `list`
  mesmo que a primeira implementacao seja em memoria - manter a assinatura
  permite trocar para streaming sem quebrar consumidores.
- `chunk_index` em CSV representa numero de linha do arquivo (excluindo
  header). Diferente do PDF, nao representa fragmento de texto. Documente
  isto no `_row_to_metadata` para nao confundir downstream.
- Encoding fallback NAO deve ser silencioso: sempre logar qual encoding
  funcionou. Em producao, isso e sinal de qualidade dos dados de entrada.
- Pandas pode mascarar campos `"NULL"`, `"None"`, `"NA"` como NaN.
  `keep_default_na=False` evita isso, mas se o cliente quiser semantica
  diferente, expor parametro no `__init__` em iteracao futura.
- O `column_mapping` deve aceitar comparacao case-insensitive em nomes de
  colunas? Por padrao, nao - mantenha estrito para evitar bugs sutis.
  Adicionar normalizacao explicita se aparecer demanda de cliente.
- AGENT.md secao 3.7 cita `slowapi` para rate limiting de API. NAO se aplica
  ao loader, mas serve de lembrete: validacao defensiva no boundary
  (`load()`) compensa confianca interna no resto do pipeline.
- Conformidade ISO 14224: cada work order vira evidencia rastreavel
  (`source_ref` -> filename + linha). Combinada com a saida do `PDFLoader`,
  forma o substrato auditavel da Fase 1.
