"""
main.py — Interactive CLI and demo entry-point for the Second Brain.

Usage:
    python main.py                    # interactive REPL
    python main.py --demo             # run the built-in demo
    python main.py --ingest file.pdf  # one-shot ingestion
"""

import argparse
import sys
import textwrap

from brain import SecondBrain


# ======================================================================
# CLI helpers
# ======================================================================

BANNER = """
╔══════════════════════════════════════════════════╗
║           🧠  Second Brain  — Local AI KB        ║
║  Type  help  for available commands              ║
╚══════════════════════════════════════════════════╝
"""

HELP_TEXT = """
Available commands
──────────────────────────────────────────────────
  ingest pdf  <path>          Ingest a PDF file
  ingest url  <url>           Ingest a web page
  ingest text                 Type / paste a note (end with END)
  ingest file <path>          Auto-detect and ingest

  ask  <question>             Ask anything
  summarize <topic>           Summarise a topic
  summarize doc <source>      Summarise a specific document
  compare <topic1> | <topic2> Compare two topics
  questions <topic>           Generate study questions

  insights                    Generate daily insights
  history                     Show recent insights
  docs                        List ingested documents
  stats                       Show knowledge base statistics
  graph build                 Build the concept knowledge graph
  graph related <concept>     Show related concepts
  graph central               Show most important concepts
  graph connect <c1> | <c2>   Find connection between concepts

  search <query>              Raw semantic search
  clear                       Clear conversation history
  help                        Show this message
  quit / exit                 Exit
──────────────────────────────────────────────────
"""


def run_repl(brain: SecondBrain):
    print(BANNER)
    while True:
        try:
            raw = input("🧠 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not raw:
            continue

        parts = raw.split(None, 2)
        cmd = parts[0].lower()

        # ── exit ──────────────────────────────────────────
        if cmd in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        # ── help ──────────────────────────────────────────
        elif cmd == "help":
            print(HELP_TEXT)

        # ── clear ─────────────────────────────────────────
        elif cmd == "clear":
            brain.clear_conversation()
            print("Conversation history cleared.")

        # ── stats ─────────────────────────────────────────
        elif cmd == "stats":
            s = brain.stats()
            print(f"\n📊 Knowledge Base Statistics")
            print(f"  Documents : {s['documents_ingested']}")
            print(f"  Chunks    : {s['total_chunks']}")
            print(f"  Graph     : {s['graph']['nodes']} nodes, "
                  f"{s['graph']['edges']} edges")
            print(f"  Sources   :")
            for src, count in s["sources"].items():
                print(f"    {count:>4}  {src}")

        # ── docs ──────────────────────────────────────────
        elif cmd == "docs":
            docs = brain.list_documents()
            if not docs:
                print("No documents ingested yet.")
            else:
                print(f"\n📚 {len(docs)} document(s) in knowledge base:")
                for d in docs:
                    print(
                        f"  [{d['source_type'].upper():4}] "
                        f"{d['source']}  "
                        f"({d['chunk_count']} chunks)  "
                        f"ingested {d['ingested_at'][:10]}"
                    )

        # ── ingest ────────────────────────────────────────
        elif cmd == "ingest":
            if len(parts) < 2:
                print("Usage: ingest pdf|url|text|file <target>")
                continue
            sub = parts[1].lower()
            target = parts[2] if len(parts) > 2 else ""

            if sub == "pdf":
                result = brain.ingest_pdf(target)
            elif sub == "url":
                result = brain.ingest_url(target)
            elif sub == "file":
                result = brain.ingest_file(target)
            elif sub == "text":
                print("Enter your text (type END on a new line to finish):")
                lines = []
                while True:
                    line = input()
                    if line.strip() == "END":
                        break
                    lines.append(line)
                label = input("Label for this note: ").strip() or "note"
                result = brain.ingest_text("\n".join(lines), label)
            else:
                print(f"Unknown ingest type '{sub}'.")
                continue
            print(f"  → {result['chunks_added']} chunks added.")

        # ── ask ───────────────────────────────────────────
        elif cmd == "ask":
            question = raw[4:].strip()
            if not question:
                print("Usage: ask <question>")
                continue
            answer = brain.ask(question)
            print(f"\n{textwrap.fill(answer, width=80)}\n")

        # ── summarize ─────────────────────────────────────
        elif cmd == "summarize":
            if len(parts) > 1 and parts[1].lower() == "doc":
                source = parts[2] if len(parts) > 2 else ""
                result = brain.summarize_document(source)
                print(f"\n{result['summary']}\n")
            else:
                topic = raw[10:].strip()
                print(brain.summarize(topic))

        # ── compare ───────────────────────────────────────
        elif cmd == "compare":
            rest = raw[8:].strip()
            if "|" not in rest:
                print("Usage: compare <topic1> | <topic2>")
                continue
            t1, t2 = [t.strip() for t in rest.split("|", 1)]
            print(brain.compare(t1, t2))

        # ── questions ─────────────────────────────────────
        elif cmd == "questions":
            topic = raw[9:].strip()
            qs = brain.generate_questions(topic)
            print(f"\nStudy questions about '{topic}':")
            for q in qs:
                print(f"  {q}")

        # ── insights ──────────────────────────────────────
        elif cmd == "insights":
            print(brain.get_insights())

        # ── history ───────────────────────────────────────
        elif cmd == "history":
            items = brain.recent_insights()
            if not items:
                print("No insights generated yet.")
            for item in items:
                print(f"\n[{item['created_at'][:10]}]\n{item['insight'][:300]}…")

        # ── search ────────────────────────────────────────
        elif cmd == "search":
            query = raw[7:].strip()
            results = brain.search(query)
            print(f"\n🔎 Top {len(results)} results for '{query}':\n")
            for i, r in enumerate(results, 1):
                print(
                    f"  {i}. [{r['relevance']:.2f}] "
                    f"{r['metadata'].get('source', '?')} — "
                    f"{r['content'][:120]}…"
                )

        # ── graph ─────────────────────────────────────────
        elif cmd == "graph":
            if len(parts) < 2:
                print("Usage: graph build | related <c> | central | connect <c1>|<c2>")
                continue
            sub = parts[1].lower()
            rest = parts[2] if len(parts) > 2 else ""

            if sub == "build":
                brain.build_knowledge_graph()
            elif sub == "related":
                concepts = brain.get_related_concepts(rest)
                print(f"Concepts related to '{rest}': {concepts}")
            elif sub == "central":
                concepts = brain.get_central_concepts()
                print("Most central concepts:")
                for concept, score in concepts:
                    print(f"  {score:.4f}  {concept}")
            elif sub == "connect":
                if "|" not in rest:
                    print("Usage: graph connect <concept1> | <concept2>")
                    continue
                c1, c2 = [c.strip() for c in rest.split("|", 1)]
                conn = brain.find_connection(c1, c2)
                print(f"\nGraph path: {' → '.join(conn['graph_path']) or 'none'}")
                print(f"\n{conn['explanation']}")
            else:
                print(f"Unknown graph sub-command '{sub}'.")

        else:
            # Treat unrecognised input as a question
            answer = brain.ask(raw)
            print(f"\n{textwrap.fill(answer, width=80)}\n")


# ======================================================================
# Demo
# ======================================================================

def run_demo(brain: SecondBrain):
    """Ingest sample content and demonstrate core features."""
    print("\n" + "=" * 60)
    print("  Second Brain — Demo Mode")
    print("=" * 60)

    # 1. Ingest a quick text note
    brain.ingest_text(
        text=(
            "Machine learning is a subset of artificial intelligence "
            "that enables systems to learn from data. Deep learning uses "
            "neural networks with many layers. Transformers are a key "
            "architecture behind modern language models like GPT and BERT. "
            "Attention mechanisms allow models to focus on relevant parts "
            "of the input sequence."
        ),
        label="ml_overview",
    )

    brain.ingest_text(
        text=(
            "The Feynman Technique is a learning method developed by "
            "physicist Richard Feynman. It involves four steps: choose a "
            "concept, teach it to a child, identify gaps, and simplify. "
            "Active recall and spaced repetition are complementary techniques "
            "for long-term retention."
        ),
        label="learning_techniques",
    )

    # 2. Ask questions
    print("\n" + "-" * 60)
    print("Q: What is the relationship between deep learning and transformers?")
    answer = brain.ask(
        "What is the relationship between deep learning and transformers?",
        verbose=True,
    )
    print(answer)

    print("\n" + "-" * 60)
    print("Q: How can I apply the Feynman Technique to learning ML?")
    answer = brain.ask(
        "How can I apply the Feynman Technique to learning ML?",
        verbose=True,
    )
    print(answer)

    # 3. Summarise a topic
    print("\n" + "-" * 60)
    print("SUMMARY: machine learning")
    print(brain.summarize("machine learning"))

    # 4. Compare topics
    print("\n" + "-" * 60)
    print("COMPARE: deep learning vs Feynman Technique")
    print(brain.compare("deep learning", "Feynman Technique"))

    # 5. Generate questions
    print("\n" + "-" * 60)
    print("QUESTIONS: transformers")
    for q in brain.generate_questions("transformers", n=3):
        print(f"  {q}")

    # 6. Daily insights
    print("\n" + "-" * 60)
    print("INSIGHTS:")
    print(brain.get_insights(n=2))

    # 7. Stats
    print("\n" + "-" * 60)
    s = brain.stats()
    print(
        f"STATS — {s['documents_ingested']} docs, "
        f"{s['total_chunks']} chunks, "
        f"{s['graph']['nodes']} graph nodes"
    )


# ======================================================================
# Entry-point
# ======================================================================

def main():
    parser = argparse.ArgumentParser(description="Second Brain — Local AI Knowledge Base")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo")
    parser.add_argument("--ingest", metavar="PATH", help="Ingest a file then exit")
    parser.add_argument("--ask", metavar="QUESTION", help="Ask a question then exit")
    parser.add_argument(
        "--model", default="mistral:7b", help="Ollama LLM model (default: mistral:7b)"
    )
    args = parser.parse_args()

    brain = SecondBrain(llm_model=args.model)

    if args.demo:
        run_demo(brain)
    elif args.ingest:
        result = brain.ingest_file(args.ingest)
        print(f"Ingested '{result['source']}' — {result['chunks_added']} chunks added.")
    elif args.ask:
        print(brain.ask(args.ask))
    else:
        run_repl(brain)


if __name__ == "__main__":
    main()