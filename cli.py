from dotenv import load_dotenv
load_dotenv()

from pipeline.enrich import enrich_ast
from pipeline.insert_graph import insert_enriched_graph
print("CLI script started")
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import argparse
from pipeline.cs_parser import parse_cs_file
from pathlib import Path
import sys
def main():
    parser = argparse.ArgumentParser(description="C# to Graph CLI Tool")
    parser.add_argument("filepath", help="Path to the C# file")
    args = parser.parse_args()
    path = Path(args.filepath)
    if not path.exists():
        print(f"[CLI] File not found: {path}")
        sys.exit(1)
    print(f"[CLI] File path received: {path}")
    try:
        ast = parse_cs_file(str(path))
        # ---- Enrich step ----
        enriched = enrich_ast(ast)
        print("[CLI] Enriched output sample:", enriched[:1])
        # ---- Graph insertion step ----
        insert_enriched_graph(enriched)
        print("[CLI] Graph insertion complete.")


    except Exception as e:
        print(f"[CLI] Parse failed: {e}")
        sys.exit(1)
    try:
        count = len(ast) if hasattr(ast, "__len__") else 1
        print(f"[CLI] Parsed AST items: {count}")
        print(f"[CLI] AST sample: {ast[:1] if hasattr(ast, '__getitem__') else ast}")
    except Exception:
        print("[CLI] Parsed AST (non-indexable).")

if __name__ == "__main__":
    main()
