
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Local AI](https://img.shields.io/badge/AI-Local%20First-orange)

```markdown
# 🧠 Second Brain

**A local, privacy‑first AI knowledge base that grows with you.**

Second Brain turns your documents, web pages, and notes into a searchable, conversational knowledge base that runs entirely on your machine. It ingests PDFs, URLs, and raw text, stores them in a vector database and a knowledge graph, then lets you query, summarize, and draw insights using a local LLM.

---
## 🤔 Why Second Brain?

Most AI tools require sending your data to the cloud.
Second Brain keeps everything local, private, and fully under your control—while still giving you powerful semantic search and reasoning.

## ✨ Features

- **📥 Multi‑format ingestion** – PDFs, web pages, text snippets, or auto‑detected files.
- **🔍 Semantic search** – Find relevant information by meaning, not just keywords.
- **💬 Conversational Q&A** – Ask questions in natural language and get answers grounded in your own data.
- **📝 Document & topic summaries** – Generate structured summaries with key points.
- **🔗 Knowledge graph** – Discover how concepts connect across your library.
- **💡 Daily insights** – Surface surprising connections between random pieces of your knowledge.
- **🖥️ Interactive CLI** – A rich REPL with history, help, and dozens of commands.
- **🔒 100% local** – Your data never leaves your machine. Uses Ollama for LLM inference and embeddings.

---

## 🏗️ Architecture

```
second_brain/
├── ingestion/          # PDF, web, and text processors
├── storage/            # Vector store, graph store, summary store
├── agents/             # Query, link, and insight reasoning agents
├── utils/              # Helpers
├── brain.py            # Main orchestrator / public API
├── main.py             # Interactive CLI entry‑point
└── Architecture.txt    # Detailed directory layout
```

The system is built around a modular pipeline:

1. **Ingestion** modules parse raw content into chunks.
2. **Storage** layers persist those chunks in a Chroma vector database, a NetworkX knowledge graph, and a SQLite summary store.
3. **Agents** use a local LLM (default: `mistral:7b`) to reason across the stored knowledge, providing answers, connections, and insights.

All components are wired together by the `SecondBrain` class in `brain.py`, which offers a simple, unified API.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.com/)** installed and running locally.
- Pull a local LLM model and an embedding model:
  ```bash
  ollama pull mistral:7b
  ollama pull nomic-embed-text
  ```
  (You can configure different models later – see [Configuration](#configuration) below.)

### Installation

```bash
# Clone the repository
git clone https://github.com/2am-dev/Second-Brain.git
cd Second-Brain

# Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

Launch the interactive REPL:

```bash
python main.py
```

You’ll see the welcome banner and a prompt. Try these commands:

```
> ingest pdf /path/to/paper.pdf
> ask What is the main contribution of this paper?
> summarize doc paper.pdf
> insights
> help
```

To ingest a web page:

```
> ingest url https://en.wikipedia.org/wiki/Knowledge_graph
```

To compare two topics:

```
> compare attention | transformer
```

For a one‑shot ingestion without entering the REPL:

```bash
python main.py --ingest /path/to/file.pdf
python main.py --demo   # run a built‑in demonstration
```

---

## 📖 CLI Commands

| Command | Description |
|---------|-------------|
| `ingest pdf <path>` | Ingest a PDF file |
| `ingest url <url>` | Ingest a web page |
| `ingest text` | Type or paste a note (end with `END`) |
| `ingest file <path>` | Auto‑detect and ingest a file |
| `ask <question>` | Ask anything about your knowledge base |
| `summarize <topic>` | Summarise a topic |
| `summarize doc <source>` | Summarise a specific document |
| `compare <a> <b>` | Compare two topics |
| `questions` | Generate study questions |
| `insights` | Generate daily insights |
| `history` | Show recent insights |
| `docs` | List ingested documents |
| `stats` | Show knowledge base statistics |
| `graph build` | Build the concept knowledge graph |
| `graph related <concept>` | Show related concepts |
| `graph central` | Show most important concepts |
| `graph connect <a> <b>` | Find connection between concepts |
| `search <query>` | Raw semantic search |
| `clear` | Clear conversation history |
| `help` | Show this message |
| `quit` / `exit` | Exit |

---

## ⚙️ Configuration

You can customize the models and storage paths by instantiating `SecondBrain` directly in your own scripts:

```python
from brain import SecondBrain

brain = SecondBrain(
    db_path="./my_vector_db",          # Chroma vector store directory
    graph_path="./my_graph.pkl",       # NetworkX graph file
    summary_db="./my_summaries.db",    # SQLite summary store
    llm_model="llama3.2:3b",           # Any Ollama model
    embed_model="nomic-embed-text",    # Embedding model
)
```

---

## 🧪 Example Script

```python
from brain import SecondBrain

# Initialize the brain
brain = SecondBrain()

# Ingest a PDF
brain.ingest_pdf("papers/transformer.pdf")

# Ask a question
answer = brain.ask("What is the key innovation of the transformer architecture?")
print(answer)

# List all documents
for doc in brain.list_documents():
    print(doc["source"], doc["chunk_count"], "chunks")

# Get daily insights
print(brain.generate_insights())
```

---

## 🛠️ Dependencies

The project is Python‑only and relies on:

- **[Chroma](https://www.trychroma.com/)** – vector database for semantic search.
- **[Ollama](https://github.com/ollama/ollama-python)** – local LLM and embedding serving.
- **[NetworkX](https://networkx.org/)** – knowledge graph manipulation.
- **[SQLite](https://www.sqlite.org/)** – lightweight summary and metadata storage.
- **[PyPDF2](https://pypi.org/project/PyPDF2/)** (or similar) – PDF text extraction.
- **[requests](https://pypi.org/project/requests/)** / **[beautifulsoup4](https://pypi.org/project/beautifulsoup4/)** – web page processing.

All can be installed via `pip install -r requirements.txt`.

---

## 🗺️ Roadmap

- [ ] Gradio/Streamlit web UI
- [ ] Scheduled background ingestion (watch folders)
- [ ] Multi‑user support
- [ ] More sophisticated graph reasoning (e.g., path‑finding between concepts)
- [ ] Integration with note‑taking apps (Obsidian, Notion)

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request. For major changes, please start a discussion first.

---

## 📜 License

MIT – see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by [2am-dev](https://github.com/2am-dev)**
```

