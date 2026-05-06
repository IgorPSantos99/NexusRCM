# PDF Loader Fixtures

PDF loader unit tests generate small synthetic PDFs at runtime with PyMuPDF.
This keeps the repository lightweight while preserving reproducible inputs:

- Text pages use `page.insert_text(...)`.
- Empty pages are blank pages with no extractable text.
- Image-only pages embed a 1x1 PNG and no text.
- Corrupted PDFs are temporary files with invalid PDF bytes.
