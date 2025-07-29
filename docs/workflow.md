## 1. Data Flow Architecture

### 1.1 Graphical Representation Of Workflow
```mermaid
graph TD
    A[C# Source Code Files] -->|Input| B[ANTLR Parser]
    B -->|Produces| C[Raw AST]
    C -->|Serialized as| D[AST JSON]
    D -->|Input to| E[Chunked LLM Enrichment Service]
    E -->|Uses| OL[Ollama Local LLM<br/>deepseek-coder:1.3b]
    E -->|Produces| F[Enriched JSON]
    F -->|Mapped to| G[Neo4j Graph Database]
    
    H[FastAPI Service] -->|Orchestrates| B
    H -->|Orchestrates| E
    H -->|Orchestrates| G
    
    I[CLI Tool] -->|Orchestrates| B
    I -->|Orchestrates| E
    I -->|Orchestrates| G
    
    subgraph "Data Transformation Pipeline"
        B
        C
        D
        E
        OL
        F
    end
    
    subgraph "Storage Layer"
        G
    end
    
    subgraph "Interface Layer"
        H
        I
    end
    
    subgraph "Local AI Infrastructure"
        OL
    end
```


### 1.2 Enhanced Chunked Enrichment Flow

```text
1. [C# Code File] (from input_code/)
    ⬇
2. [ANTLR Parser] 
    ➤ Uses C# grammar to generate an Abstract Syntax Tree (AST)
    ➤ Identifies classes, methods, properties, etc.
    ➤ Outputs list of nodes with type, name, and line number
    ⬇
3. [JSON Serialization] 
    ➤ Serialize AST nodes into a clean JSON structure 
    ➤ Writes to parsed_output/file_ast.json
    ⬇
4. [Chunked LLM Enrichment] 
    ➤ Extracts class and method chunks from AST
    ➤ Processes classes separately for class-level metadata
    ➤ Processes methods individually for method-level insights
    ➤ Uses local Ollama API (deepseek-coder:1.3b) for security
    ➤ Combines original AST with structured enrichments
    ⬇
5. [Neo4j Insertion]
    ➤ Maps enriched JSON to graph schema defined in models.py
    ➤ Creates CodeEntity nodes for classes, methods, etc.
    ➤ Establishes relationships: CONTAINS, DEPENDS_ON
    ➤ Stores enriched metadata as node properties
    ⬇
6. [Neo4j Graph Database]
    ➤ Final result is a visual and queryable graph:
        - Nodes: Code entities (classes, methods, etc.)
        - Edges: Dependencies, containment, call graphs
        - Properties: Line numbers, summaries, tags, enriched metadata
```
