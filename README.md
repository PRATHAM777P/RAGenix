# RAGenix — Advanced RAG Agent

```
██████╗  █████╗  ██████╗ ███████╗███╗   ██╗██╗██╗  ██╗
██╔══██╗██╔══██╗██╔════╝ ██╔════╝████╗  ██║██║╚██╗██╔╝
██████╔╝███████║██║  ███╗█████╗  ██╔██╗ ██║██║ ╚███╔╝ 
██╔══██╗██╔══██║██║   ██║██╔══╝  ██║╚██╗██║██║ ██╔██╗ 
██║  ██║██║  ██║╚██████╔╝███████╗██║ ╚████║██║██╔╝ ██╗
╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═╝
           Advanced Retrieval-Augmented Generation
```

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://python.org)
[![Chainlit](https://img.shields.io/badge/Chainlit-0.7.604-green)](https://chainlit.io)
[![LangChain](https://img.shields.io/badge/LangChain-0.0.340-orange)](https://langchain.com)

---

## Overview

**RAGenix** is a production-grade Retrieval-Augmented Generation (RAG) agent that lets you chat with your PDF documents. It combines hybrid lexical + semantic search with Cohere reranking to deliver precise, source-cited answers.

### Key Features

| Feature | Description |
|---|---|
| 📄 **Multi-PDF Upload** | Upload up to 3 PDFs simultaneously |
| 🔀 **Hybrid Search** | BM25 (lexical) + Qdrant (dense vector) ensemble retrieval |
| 🎯 **Cohere Reranking** | Contextual compression for top-quality chunk selection |
| 💬 **Conversation Memory** | Follow-up questions with 5-turn rolling context window |
| 📌 **Source Citations** | Every answer includes traceable chunk references |
| ⚡ **GPU / CPU Adaptive** | Automatically uses CUDA if available, falls back to CPU |
| 🌊 **Streaming Answers** | Real-time token streaming via Chainlit |
| 🛡️ **Secure Credentials** | `.env`-based secrets, no hardcoded paths or keys |

---

## Architecture

```
User Upload (PDF)
      │
      ▼
  Text Extraction (PyPDF2)
      │
      ▼
  Chunking (RecursiveCharacterTextSplitter, 1000 tok / 100 overlap)
      │
      ├─────────────────────┐
      ▼                     ▼
 BM25 Retriever       Qdrant In-Memory
  (lexical)          (dense embeddings)
      │                     │
      └──────┬──────────────┘
             ▼
     EnsembleRetriever (50/50 weight)
             │
             ▼
    CohereRerank Compressor
             │
             ▼
   ConversationalRetrievalChain
       (Azure OpenAI LLM)
             │
             ▼
     Streaming Answer + Sources
```

---

## Quickstart

### 1. Clone & Install

```bash
git clone https://github.com/PRATHAM777P/RAGenix.git
cd RAGenix
pip install -r requirements.txt
```

### 2. Configure Credentials

```bash
cp .env.example .env
# Edit .env and fill in your Azure OpenAI and Cohere credentials
```

Your `.env` file should look like:

```env
OPENAI_API_TYPE=azure
AZURE_OPENAI_VERSION=2023-05-15
AZURE_OPENAI_BASE=https://YOUR_RESOURCE.openai.azure.com/
AZURE_OPENAI_KEY=sk-...
AZURE_DEPLOYMENT_NAME=gpt-35-turbo
AZURE_ENGINE=gpt-35-turbo
COHERE_API_KEY=co-...
```

> ⚠️ **Never commit `.env` to version control.** It is in `.gitignore`.

### 3. Run

```bash
chainlit run app.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Project Structure

```
RAGenix/
├── app.py                  # Main Chainlit app (upload, QA, streaming)
├── configure_models.py     # Model init (LLM, embeddings, reranker)
├── requirements.txt        # Python dependencies
├── .gitignore              # Excludes .env, __pycache__, data/, etc.
├── LICENSE                 # Apache 2.0
├── README.md               # This file
├── SECURITY.md             # Vulnerability disclosure policy
├── .chainlit/
│   └── config.toml         # Chainlit UI/feature configuration
└── data/                   # Optional: local reference documents
```

---

## Configuration

Edit `.chainlit/config.toml` to customize the UI:

```toml
[UI]
name = "RAGenix"

[features]
multi_modal = true          # Allow file uploads
prompt_playground = true    # Show prompt inspector
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push and open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/).

---

## Security

See [SECURITY.md](SECURITY.md) for our vulnerability disclosure policy.

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
