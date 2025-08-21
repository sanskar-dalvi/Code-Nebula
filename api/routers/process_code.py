from fastapi import APIRouter
from pydantic import BaseModel
from pipeline.cs_parser import parse_cs_file
from pipeline.enrich import enrich_ast
from pipeline.insert_graph import insert_enriched_graph

router = APIRouter()

class FileRequest(BaseModel):
    filepath: str

@router.post("/process")
def process_code(request: FileRequest):
    path = request.filepath

    # Parse
    ast = parse_cs_file(path)

    # Enrich
    enriched = enrich_ast(ast)

    # Insert
    insert_enriched_graph(enriched)

    return {"status": "success", "nodes": len(enriched)}

