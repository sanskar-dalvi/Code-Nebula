def enrich_ast(ast):
    """
    Temporary stub for AI enrichment.
    Later this will call the LLM and return summaries/tags.
    """
    print("[Enrich] Pretending to enrich AST...")
    enriched = []
    for node in ast:
        node["summary"] = "This is a sample summary."
        node["tags"] = ["demo", "stub"]
        enriched.append(node)
    return enriched

