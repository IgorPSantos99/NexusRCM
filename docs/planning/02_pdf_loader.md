# Checklist de Implementacao - PDF Loader (PyMuPDF)

Use este arquivo como lista unica de acompanhamento para implementar o
`PDFLoader`, primeiro componente concreto da camada de ingestao. O loader
materializa o contrato `BaseLoader` definido em `src/nexusrcm/interfaces.py`
([interfaces.py](../../src/nexusrcm/interfaces.py)) e e a porta de entrada
de todo o pipeline downstream (NLP -> grafo -> retrieval).

* branch sugerida: `feat/pdf-loader`
* fase do roadmap: Fase 1 - Semanas 1 e 2 (Data Pipeline)
* dependencias ja existentes: `PyMuPDF>=1.24,<2.0`, `pydantic>=2.7,<3.0`
* contrato a respeitar: `BaseLoader` Protocol em
  [interfaces.py:142](../../src/nexusrcm/interfaces.py#L142)
* excecao a propagar: `LoaderError` em
  [exceptions.py](../../src/nexusrcm/exceptions.py)

> **Por que PyMuPDF e nao PyPDF/pdfplumber?** PyMuPDF (`fitz`) e o parser
> puro-Python mais rapido para PDFs textuais e expoe metadados de pagina
> diretamente. Limitacoes (PDFs escaneados, layouts complexos com tabelas)
> serao tratadas por Docling/OCR em ADR futura. Esta fase resolve o caminho
> feliz: PDFs textuais bem formados.

---

## Escopo Obrigatorio

### Configuracao e Settings

- [ ] 1. Criar `src/nexusrcm/config.py` com `pydantic-settings`.
  - [ ] 1.1. Definir `class Settings(BaseSettings)` com prefixo `NEXUSRCM_`.
  - [ ] 1.2. Adicionar `pdf_chunk_size_tokens: int = 512`.
  - [ ] 1.3. Adicionar `pdf_chunk_overlap_tokens: int = 64`.
  - [ ] 1.4. Adicionar `pdf_max_file_size_bytes: int = 50 * 1024 * 1024` (50 MB).
  - [ ] 1.5. Adicionar `pdf_min_text_chars_per_page: int = 10` (limite para detectar pagina image-only).
  - [ ] 1.6. Adicionar `field_validator` que rejeita `pdf_chunk_overlap_tokens >= pdf_chunk_size_tokens`.
  - [ ] 1.7. Exportar `get_settings()` cacheada com `functools.lru_cache`.
  - [ ] 1.8. Documentar variaveis no `.env.example` (criar se nao existir).

> **Por que Settings?** AGENT.md secao 2.5: nada de magic numbers. Um unico
> ponto de configuracao com validacao Pydantic evita que o usuario passe
> overlap maior que chunk_size e quebre a tokenizacao silenciosamente.
>
> **Cuidado de portabilidade/teste:** nao chame `get_settings()` em import time
> para preencher atributos de classe. Isso congela variaveis de ambiente antes
> dos testes conseguirem sobrescreve-las. Use constantes default estaveis para
> introspeccao de classe e resolva Settings no `__init__`.

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

`pdf_loader.py` e `csv_loader.py` ficam separados porque PDF e CSV tem
semanticas diferentes: PDF e documento paginado; CSV e tabela de eventos.
O modulo privado `_validation.py` concentra apenas validacoes compartilhadas
de arquivo para evitar duplicacao entre loaders.

- [ ] 2. Criar `src/nexusrcm/ingestion/pdf_loader.py`.
  - [ ] 2.1. Definir docstring de modulo explicando proposito (Google style).
  - [ ] 2.2. Importar `fitz` (PyMuPDF) protegido contra ausencia em runtime
        (mensagem clara de instalacao via `pyproject.toml`).
  - [ ] 2.3. Importar `BaseLoader`, `DocumentChunk`, `SourceRef` de `nexusrcm.interfaces`.
  - [ ] 2.4. Importar `LoaderError` de `nexusrcm.exceptions`.
  - [ ] 2.5. Importar `logging` e instanciar `logger = logging.getLogger(__name__)`.
        AGENT.md secao 2.5: nada de `print()`.
  - [ ] 2.6. Adicionar `__all__ = ["PDFLoader"]`.

#### Validacoes compartilhadas

- [ ] 2A. Criar `src/nexusrcm/ingestion/_validation.py` como modulo privado.
  - [ ] 2A.1. Definir docstring de modulo explicando que os helpers sao internos da camada de ingestao.
  - [ ] 2A.2. Criar helper `_ensure_path_source(source: Path) -> None` para rejeitar `str` e outros tipos.
  - [ ] 2A.3. Criar helper `_validate_existing_file(source: Path) -> None` para existencia, arquivo regular e permissao.
  - [ ] 2A.4. Criar helper `_validate_supported_extension(source: Path, supported_extensions: frozenset[str]) -> None` com comparacao case-insensitive.
  - [ ] 2A.5. Criar helper `_validate_file_size(source: Path, max_file_size_bytes: int) -> int` retornando tamanho real.
  - [ ] 2A.6. Todos os helpers devem converter falhas operacionais para `LoaderError`.
  - [ ] 2A.7. Manter `__all__ = []` ou nao exportar nada; consumers externos nao devem depender desse modulo.

> **Por que `_validation.py` agora?** PDF e CSV precisam das mesmas guardas:
> tipo, existencia, extensao e tamanho. Centralizar isso evita dois loaders com
> mensagens de erro divergentes e reduz manutencao quando o contrato mudar.

- [ ] 3. Atualizar `src/nexusrcm/ingestion/__init__.py`.
  - [ ] 3.1. Reexportar `PDFLoader` no `__all__` do pacote.
  - [ ] 3.2. Manter ordem alfabetica nas exportacoes futuras.

### Classe `PDFLoader`

- [ ] 4. Definir atributos de classe exigidos pelo Protocol.
  - [ ] 4.1. `supported_extensions: frozenset[str] = frozenset({".pdf"})`.
  - [ ] 4.2. `max_file_size_bytes: int = 50 * 1024 * 1024` como default estavel de classe para introspeccao antes de instanciar.
  - [ ] 4.3. Documentar que a comparacao de extensao e case-insensitive (`.PDF`, `.Pdf`).
  - [ ] 4.4. Definir `DEFAULT_PDF_MAX_FILE_SIZE_BYTES` no modulo ou em `config.py` para evitar magic number duplicado.

- [ ] 5. Implementar `__init__` configuravel.
  - [ ] 5.1. Aceitar `chunk_size: int | None = None` e `chunk_overlap: int | None = None`.
  - [ ] 5.2. Resolver defaults via `get_settings()` quando os parametros forem `None`.
  - [ ] 5.3. Validar `chunk_overlap < chunk_size` (`raise ValueError` em construcao, nao `LoaderError`).
  - [ ] 5.4. Persistir `self._chunk_size` e `self._chunk_overlap` como atributos privados.
  - [ ] 5.5. Resolver `self.max_file_size_bytes` a partir de `Settings.pdf_max_file_size_bytes` na instancia, sem alterar o default de classe.

- [ ] 6. Implementar `load(self, source: Path) -> Iterator[DocumentChunk]` como generator.
  - [ ] 6.1. Reutilizar helpers de `_validation.py` para validar tipo, existencia, extensao e tamanho.
  - [ ] 6.2. Validar que `source` e instancia de `Path` (defensivo contra `str`) via `_ensure_path_source`.
  - [ ] 6.3. Validar existencia do arquivo; se ausente, `raise LoaderError(source, "file not found")`.
  - [ ] 6.4. Validar extensao em `supported_extensions` (lowercase); caso contrario `LoaderError`.
  - [ ] 6.5. Validar `source.stat().st_size <= max_file_size_bytes`; caso contrario `LoaderError` com mensagem citando tamanho real e limite.
  - [ ] 6.6. Abrir o PDF com `fitz.open(source)` dentro de `try/except` capturando
        `fitz.FileDataError` e `RuntimeError`; converter em `LoaderError` com `reason` claro.
  - [ ] 6.7. Garantir fechamento do documento via `with contextlib.closing(...)` ou bloco try/finally.
  - [ ] 6.8. Iterar paginas com `for page_index, page in enumerate(doc)` (zero-based interno).
  - [ ] 6.9. Extrair texto com `page.get_text("text")` (modo plain).
  - [ ] 6.10. Detectar pagina image-only (`len(text.strip()) < settings.pdf_min_text_chars_per_page`)
        e logar `logger.warning("image-only page skipped", extra={...})` SEM levantar excecao.
  - [ ] 6.11. Aplicar normalizacao minima: `text = text.strip()` antes de tokenizar.
  - [ ] 6.12. Para cada chunk gerado dentro da pagina, montar `SourceRef(filename=source.name, page=page_index + 1, chunk_index=local_chunk_index)`.
  - [ ] 6.13. `yield DocumentChunk(text=chunk_text, source_ref=ref, metadata={"loader": "pdf", "total_pages": doc.page_count})`.
  - [ ] 6.14. Retornar (encerrar generator) sem levantar excecao quando o PDF for valido mas sem texto.

> **Por que generator?** O contrato exige `Iterator[DocumentChunk]`
> ([interfaces.py:153](../../src/nexusrcm/interfaces.py#L153)). PDFs grandes
> (centenas de paginas) geram milhares de chunks; manter tudo em memoria
> antes de embeddar e desperdicio. Generator permite pipeline streaming.

### Estrategia de chunking

- [ ] 7. Implementar funcao auxiliar `_chunk_page_text(text: str) -> Iterator[str]`.
  - [ ] 7.1. Tokenizar por whitespace simples (`text.split()`) como aproximacao de tokens.
  - [ ] 7.2. Documentar no docstring que isto NAO e BPE/sentencepiece e sera substituivel
        quando o extractor usar tokenizer real.
  - [ ] 7.3. Iterar com janela deslizante: `start = 0`, passo `chunk_size - chunk_overlap`.
  - [ ] 7.4. Reconstruir cada chunk com `" ".join(tokens[start:start + chunk_size])`.
  - [ ] 7.5. Garantir que paginas com menos tokens que `chunk_size` produzem exatamente um chunk.
  - [ ] 7.6. Garantir que paginas vazias produzem zero chunks (nao levantar `ValueError` do `DocumentChunk`).
  - [ ] 7.7. Numerar `chunk_index` localmente por pagina, comecando em 0.

> **Decisao explicita: chunk respeita fronteira de pagina.** Misturar texto
> entre paginas tornaria `source_ref.page` ambiguo. Auditabilidade
> (AGENT.md principio 3) exige rastreabilidade exata. Custo: chunks de paginas
> curtas tem menos contexto. Beneficio: cada citacao aponta para uma unica
> pagina verificavel.

### Tratamento de erros e logs

- [ ] 8. Mapear todas as falhas operacionais para `LoaderError`.
  - [ ] 8.1. Arquivo inexistente -> `reason="file not found"`.
  - [ ] 8.2. Extensao nao suportada -> `reason="unsupported extension '<ext>'"`.
  - [ ] 8.3. Arquivo acima do limite -> `reason="file size <N> bytes exceeds limit <M>"`.
  - [ ] 8.4. PDF corrompido / encriptado -> `reason="corrupted or encrypted pdf: <orig msg>"`.
  - [ ] 8.5. Permissao negada -> `reason="permission denied"`.
  - [ ] 8.6. Garantir que NENHUMA excecao crua de `fitz` escape do `load()`.

- [ ] 9. Adicionar logs estruturados nos pontos chave.
  - [ ] 9.1. `logger.info` ao iniciar load com filename e tamanho.
  - [ ] 9.2. `logger.warning` para cada pagina image-only descartada, com numero da pagina.
  - [ ] 9.3. `logger.info` no final do load com numero total de chunks emitidos.
  - [ ] 9.4. NAO logar conteudo do texto extraido (privacidade / volume).

### Testes (TDD - escrever antes da implementacao)

- [ ] 10. Criar `tests/fixtures/` com PDFs sinteticos versionados.
  - [ ] 10.1. `sample_manual.pdf` - 3 paginas de texto OEM-like (gerar com PyMuPDF na conftest se for grande).
  - [ ] 10.2. `empty.pdf` - 1 pagina sem texto (apenas placeholder branco).
  - [ ] 10.3. `image_only.pdf` - 1 pagina com imagem embutida e zero texto extraivel.
  - [ ] 10.4. `mixed_pages.pdf` - alternando paginas com texto e image-only.
  - [ ] 10.5. `corrupted.pdf` - bytes truncados para forcar `FileDataError`.
  - [ ] 10.6. PDFs pequenos podem ser gerados em fixtures pytest; PDFs maiores ficam versionados em `tests/fixtures/`.
  - [ ] 10.7. Documentar como cada fixture foi gerada (script reproduzivel ou comentario).

- [ ] 11. Criar `tests/test_pdf_loader.py` com cobertura por cenario.
  - [ ] 11.1. `test_supported_extensions_contains_pdf` - sanity check do contrato.
  - [ ] 11.2. `test_load_returns_iterator_not_list` - validar que retorno e generator (`isinstance(result, Iterator)` e `not isinstance(result, list)`).
  - [ ] 11.3. `test_load_happy_path_yields_chunks_with_source_ref` - verificar `filename`, `page` (1-indexed), `chunk_index` e `metadata`.
  - [ ] 11.4. `test_load_preserves_page_numbering` - garantir que pagina 1 emite chunks com `page=1`, etc.
  - [ ] 11.5. `test_load_chunk_index_resets_per_page` - segunda pagina comeca em `chunk_index=0`.
  - [ ] 11.6. `test_load_respects_chunk_size_and_overlap` - parametrizar com `(256, 32)`, `(128, 16)` e validar tamanhos.
  - [ ] 11.7. `test_load_missing_file_raises_loader_error` - assertar `exc.source` e `exc.reason`.
  - [ ] 11.8. `test_load_unsupported_extension_raises_loader_error` - tentar `.txt`, `.docx`.
  - [ ] 11.9. `test_load_oversized_file_raises_loader_error` - mockar `Path.stat` ou criar fixture grande temporaria.
  - [ ] 11.10. `test_load_corrupted_pdf_raises_loader_error` - usar `corrupted.pdf`.
  - [ ] 11.11. `test_load_empty_pdf_returns_empty_iterator` - sem chunks, sem excecao.
  - [ ] 11.12. `test_load_image_only_page_logs_warning_and_skips` - capturar com `caplog` em `WARNING` level.
  - [ ] 11.13. `test_load_mixed_pages_only_text_pages_produce_chunks` - validar que paginas image-only nao geram chunk.
  - [ ] 11.14. `test_load_does_not_leak_fitz_exceptions` - parametrizar `fitz.FileDataError`, `RuntimeError`.
  - [ ] 11.15. `test_load_is_lazy` - consumir apenas o primeiro chunk e validar que arquivo ainda esta aberto (ou que generator funciona com `next()`).
  - [ ] 11.16. `test_load_case_insensitive_extension` - `.PDF` e `.Pdf` sao aceitos.
  - [ ] 11.17. `test_constructor_rejects_overlap_geq_chunk_size` - `ValueError` em construcao.

- [ ] 12. Adicionar fixtures compartilhadas em `tests/conftest.py`.
  - [ ] 12.1. `sample_pdf_path` retornando `Path` para `sample_manual.pdf`.
  - [ ] 12.2. `tmp_pdf_factory` para gerar PDFs ad-hoc com PyMuPDF dentro de `tmp_path`.
  - [ ] 12.3. Reutilizar fixtures em `test_pdf_loader.py` e em futuro `test_pipeline_integration.py`.

### Verificacao

- [ ] 13. Rodar `ruff format` e `ruff check src tests`.
  - [ ] 13.1. Corrigir todas as ofensas (`E`, `F`, `I`, `B`, `UP`).
  - [ ] 13.2. Garantir line length <= 88.

- [ ] 14. Rodar `mypy --strict src/nexusrcm/ingestion/pdf_loader.py`.
  - [ ] 14.1. Anotar tipos completos (incluindo retorno de helpers privados).
  - [ ] 14.2. Tratar `fitz` como `Any` apenas se necessario (PyMuPDF nao tem stubs oficiais);
        documentar com `# type: ignore[import-untyped]` localizado, nao global.

- [ ] 15. Rodar `pytest --cov=src/nexusrcm/ingestion/pdf_loader`.
  - [ ] 15.1. Atingir cobertura >= 90% no modulo (loaders sao infraestrutura, alto valor).
  - [ ] 15.2. Garantir que CI continua verde (sem regressao em `test_interfaces.py`).

- [ ] 16. Validar conformidade com o Protocol em runtime.
  - [ ] 16.1. Adicionar `assert isinstance(PDFLoader(), BaseLoader)` em teste dedicado.
  - [ ] 16.2. O Protocol e `runtime_checkable`
        ([interfaces.py:141](../../src/nexusrcm/interfaces.py#L141)), entao a checagem funciona.

---

## Escopo Opcional / Portfolio

- [ ] 17. Avaliar fallback Docling para layouts complexos.
  - [ ] 17.1. Pesquisar API publica do Docling (instalacao, dependencias).
  - [ ] 17.2. NAO implementar nesta fase; criar issue `enhancement` rastreando.
  - [ ] 17.3. Documentar gatilho: PDFs com tabelas multi-coluna onde PyMuPDF entrega texto desordenado.

- [ ] 18. Adicionar metadado de extracao por chunk.
  - [ ] 18.1. Incluir `extraction_method: "pymupdf"` em `metadata` para diferenciar de loaders futuros.
  - [ ] 18.2. Incluir `pdf_metadata: {title, author}` quando disponivel via `doc.metadata`.

- [ ] 19. Telemetria de ingestao.
  - [ ] 19.1. Emitir contador de chunks via `logger` estruturado para futuro consumo de observability.
  - [ ] 19.2. NAO acoplar a sistema de metricas externo nesta fase.

- [ ] 20. Tokenizer real (HuggingFace) opcional.
  - [ ] 20.1. Permitir injetar callable `tokenize: Callable[[str], list[str]]` no construtor.
  - [ ] 20.2. Default continua `str.split` para evitar dependencia pesada.
  - [ ] 20.3. Documentar trade-off: tokenizacao alinhada com modelo NER da Fase 1 melhora limites de chunk.

---

## Ordem Recomendada

1. Criar `config.py` com `Settings` e validacao.
2. Criar `_validation.py` com guardas compartilhadas de arquivo.
3. Criar fixtures de PDFs sinteticos e helpers em `conftest.py`.
4. Escrever `tests/test_pdf_loader.py` (TDD - todos os testes falhando primeiro).
5. Implementar `PDFLoader` minimo ate o caminho feliz passar.
6. Adicionar tratamento de erros e logs ate cobrir todos os cenarios negativos.
7. Implementar `_chunk_page_text` e parametrizar tamanhos.
8. Detectar paginas image-only e logar warnings.
9. Rodar `ruff`, `mypy --strict`, `pytest --cov`.
10. Atualizar `ingestion/__init__.py` e validar `isinstance(PDFLoader(), BaseLoader)`.
11. Comitar em ordem TDD: `test(ingestion): ...` antes de `feat(ingestion): ...`.

---

## Observacoes Tecnicas

- PyMuPDF nao tem stubs de tipo oficiais. Use `# type: ignore[import-untyped]`
  localizado no import e tipe os retornos manualmente; nao desabilite mypy global.
- `fitz.open` aceita `Path` ou `str`; padronize Path em todo o codigo do projeto.
- `page.get_text("text")` e mais rapido que `"blocks"` mas perde estrutura.
  Para Fase 1 e suficiente; layouts complexos serao tratados em ADR futura.
- PDFs com senha levantam `fitz.FileDataError` ou exigem `doc.authenticate(...)`.
  Trate como corrompido nesta fase; suporte a senha e item de backlog.
- Generator significa que excecoes no meio da iteracao param o consumidor.
  Loaders devem decidir cedo (na abertura do arquivo) se vao falhar; falhas no
  meio das paginas devem ser logadas e a pagina pulada, nao propagadas.
- Pagina e 1-indexed na interface publica (`source_ref.page = 1` para a primeira
  pagina). Internamente PyMuPDF usa 0-indexed; nao vaze isso para o consumidor.
- O contrato `BaseLoader` exige `supported_extensions` e `max_file_size_bytes`
  como atributos de classe ([interfaces.py:150](../../src/nexusrcm/interfaces.py#L150)).
  Nao mover para instancia, ou orquestracao nao consegue inspecionar antes de instanciar.
- Conformidade ISO 14224: cada chunk de PDF gera evidencia rastreavel
  (`source_ref` -> filename + page). Esta e a base auditavel exigida pela
  AGENT.md principio 3 ("Auditable by default").
