# LlamaIndex Knowledge Adapter

The third real provider adapter wraps an application-created LlamaIndex index.

## Supported operations
- Ingest up to 100 text documents with optional metadata using the injected index's insert method.
- Retrieve up to 20 nodes using as_retriever(similarity_top_k=...).retrieve(query).
- Returns node text, score and metadata as untrusted context data.
- Retrieval-only: it does not call a response synthesizer or LLM.

## Dependency boundary
- The application constructs the index, embedding model, storage context and vector store.
- The adapter lazily imports llama_index.core.Document only when ingestion is used.
- Install only the exact LlamaIndex core and selected integration packages needed by the chosen deployment; do not default to the broad starter bundle.

## Limitations
- The adapter requires an existing compatible index instance; it does not build, persist, reload or migrate an index.
- Text-only ingestion/retrieval; no image/audio or multimodal nodes.
- No metadata filter, reranking, query engine, document deletion/update, batching pipeline, or async operation.
- Retrieved text and metadata remain untrusted input and must not be treated as instructions.
- Actual integration tests against a pinned LlamaIndex release and selected embedding/vector-store stack remain required.

## Test method
Tests use a small in-memory fake index to validate adapter contracts without installing LlamaIndex or making network calls.
