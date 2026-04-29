<div align="center">

![Second Brain Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=Second%20Brain&fontSize=80&fontColor=fff&animation=twinkling&fontAlignY=35&desc=Your%20Local%20AI%20Knowledge%20Base&descAlignY=55&descSize=20)

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Ollama](https://img.shields.io/badge/Powered%20by-Ollama-ff6b35?style=for-the-badge&logo=llama&logoColor=white)](https://ollama.com)
[![Local AI](https://img.shields.io/badge/AI-100%25%20Local-8b5cf6?style=for-the-badge&logo=homeassistant&logoColor=white)](https://ollama.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-ec4899?style=for-the-badge&logo=github&logoColor=white)](https://github.com/2am-dev/Second-Brain/pulls)

<br/>

**Turn your documents, web pages, and notes into a conversational AI knowledge base — that runs entirely on your machine.**

[🚀 Quick Start](#quick-start) · [✨ Features](#features) · [📖 CLI Reference](#cli-reference) · [⚙️ Configuration](#configuration) · [🗺️ Roadmap](#roadmap)

<br/>

> 🔒 **Your data never leaves your machine. No API keys. No subscriptions. No cloud.**

</div>

---

## 📸 Preview

<div align="center">
<pre>
┌─────────────────────────────────────────────────────────────────┐
│ 🧠 SECOND BRAIN                                                 │
│ Your Local AI Knowledge Base                                    │
│─────────────────────────────────────────────────────────────────│
│ ✅ Vector DB │ 1,247 chunks across 14 documents                 │
│ ✅ Knowledge Graph │ 89 concepts · 214 connections              │
│ ✅ LLM Ready │ mistral:7b via Ollama                            │
└─────────────────────────────────────────────────────────────────┘
</pre>
</div>

ask What connects the transformer architecture to attention theory?

🤔 Thinking...

💡 Based on your knowledge base:
The transformer architecture fundamentally reimagines attention as
a first-class computational primitive rather than an auxiliary
mechanism. Across your 3 related documents, the key insight is...

_


---

## 🤔 Why Second Brain?

Most AI tools require sending your data to the cloud. **Second Brain is different.**

| | ☁️ Cloud AI Tools | 🧠 Second Brain |
|---|---|---|
| **Privacy** | Data sent to remote servers | 100% local — never leaves your machine |
| **Cost** | Monthly subscriptions / API fees | Free forever |
| **Knowledge Source** | Generic world knowledge | *Your* documents and notes |
| **Connectivity** | Requires internet | Works fully offline |
| **Customization** | Limited | Fully open and configurable |
| **Data Control** | Vendor-dependent | You own everything |

---

## ✨ Features

### 📥 Multi-Format Ingestion
Ingest PDFs, web pages, raw text notes, or any auto-detected file. The pipeline chunks, cleans, and embeds everything automatically.

### 🔍 Semantic Search
Find information by *meaning*, not keywords. Ask vague questions and still get the right answer.

### 💬 Conversational Q&A
Ask natural language questions grounded entirely in your own ingested knowledge base.

### 📝 Smart Summaries
Generate structured, bullet-pointed summaries for any topic or specific document in your library.

### 🔗 Knowledge Graph
Automatically map how concepts connect across your entire library. Visualize your mental model.

### 💡 Daily Insights
Surface surprising, non-obvious connections between random pieces of your knowledge.

### 🖥️ Rich Interactive CLI
A full REPL with command history, inline help, and over 20 built-in commands.

### 🔒 100% Local & Private
Powered by Ollama. No API keys, no cloud, no telemetry — ever.

---

## 🏗️ Architecture

````markdown
second_brain/
├── ingestion/
│   ├── __init__.py
│   ├── pdf_processor.py
│   ├── web_processor.py
│   └── text_processor.py
├── storage/
│   ├── __init__.py
│   ├── vector_store.py
│   ├── graph_store.py
│   └── summary_store.py
├── agents/
│   ├── __init__.py
│   ├── query_agent.py
│   ├── link_agent.py
│   └── insight_agent.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
├── brain.py
└── main.py
````
---


## 🚀 Quick Start

### 1 · Prerequisites
````markdown
- Python 3.10+
- Ollama installed and running
````
---

### 2 · Pull Models

```bash
ollama pull mistral:7b
ollama pull nomic-embed-text
````

---

### 3 · Install

```bash
git clone https://github.com/2am-dev/Second-Brain.git
cd Second-Brain
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### 4 · Run

```bash
python main.py
python main.py --demo  #For running demo no extra files

# Ingest a single file then exit
python main.py --ingest /path/to/paper.pdf
python main.py --ingest /path/to/notes.md
python main.py --ingest /path/to/book.txt
```

---

## 📖 CLI Reference

### 📥 Ingestion

| Command              | Description                              |
| -------------------- | ---------------------------------------- |
| `ingest pdf <path>`  | Ingest a PDF file                        |
| `ingest url <url>`   | Ingest a web page                        |
| `ingest text`        | Type or paste a note (end with `END`)    |
| `ingest file <path>` | Auto‑detect format and ingest            |

---

### 🔍 Queries & Insights

| Command                         | Description                                   |
| ------------------------------- | --------------------------------------------- |
| `ask <question>`                | Ask anything about your knowledge base       |
| `search <query>`                | Raw semantic search                          |
| `summarize <topic>`             | Summarise a concept or topic                 |
| `summarize doc <source>`        | Summarise a specific ingested document       |
| `compare <a> \| <b>`            | Compare two topics or documents              |
| `questions`                     | Generate study questions from your data      |
| `insights`                      | Generate daily cross‑topic insights          |

---

### 🧠 Knowledge Graph

| Command                       | Description                                 |
| ----------------------------- | ------------------------------------------- |
| `graph build`                 | Build the concept graph from ingested content |
| `graph related <concept>`     | Show concepts most related to the given one   |
| `graph central`               | Show the most central / important concepts    |
| `graph connect <a> <b>`       | Trace the connection between two concepts     |

---

### 🛠️ Utilities

| Command           | Description                          |
| ----------------- | ------------------------------------ |
| `docs`            | List all ingested documents          |
| `stats`           | Display knowledge base statistics    |
| `history`         | Show recent insights                 |
| `clear`           | Clear current conversation context   |
| `help`            | Show the full command help           |
| `quit` / `exit`   | Exit the REPL                        |

### ⚙️ Configuration

```python
from brain import SecondBrain

brain = SecondBrain(
    db_path="./my_vector_db",
    graph_path="./my_graph.pkl",
    summary_db="./my_summaries.db",
    llm_model="llama3.2:3b",
    embed_model="nomic-embed-text",
)
```

---

## 🗺️ Roadmap

* Web UI
* Folder watcher
* Graph visualization
* Notion/Obsidian sync
* Plugin system



🤝 Contributing

PRs welcome! Open an issue or discussion first.

📜 License

MIT License — see LICENSE file.

<div align="center">

Built with ❤️ by 2am-dev

⭐ Star the repo if you find it useful!

</div> 
