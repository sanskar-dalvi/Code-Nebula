import os
import requests
from dotenv import load_dotenv

load_dotenv()

def enrich_ast(ast):
    mock_mode = os.getenv("MOCK_ENRICHMENT", "true").lower() == "true"

    if mock_mode:
        print("[Enrich] Pretending to enrich AST (MOCK_ENRICHMENT=true)...")
        enriched = []
        for node in ast:
            node["summary"] = "This is a sample summary."
            node["tags"] = ["demo", "stub"]
            enriched.append(node)
        return enriched

    # --- Real enrichment with Ollama ---
    print("[Enrich] Querying Ollama for enrichment...")

    model = os.getenv("LLM_MODEL", "deepseek-coder:1.3b")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    enriched = []
    for node in ast:
        prompt = f"Summarize the purpose of this C# entity:\n{node}"
        try:
            with requests.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt},
                stream=True,
                timeout=120
            ) as r:
                r.raise_for_status()
                output_chunks = []
                for line in r.iter_lines():
                    if line:
                        try:
                            data = line.decode("utf-8")
                            if '"response"' in data:
                                # Extract text safely
                                import json
                                parsed = json.loads(data)
                                output_chunks.append(parsed.get("response", ""))
                        except Exception:
                            continue
                text = "".join(output_chunks).strip()

            node["summary"] = text or "No summary generated"
            node["tags"] = ["generated"]

        except Exception as e:
            node["summary"] = f"Enrichment failed: {e}"
            node["tags"] = ["error"]

        enriched.append(node)

    return enriched
