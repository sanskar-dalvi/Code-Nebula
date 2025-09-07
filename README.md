# C# → Neo4j Code Graph Extractor

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.26+-green.svg)](https://neo4j.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-red.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive pipeline that extracts semantic relationships from legacy **C# (.NET 4.0)** codebases and stores them as queryable graphs in **Neo4j**. The system combines deterministic ANTLR parsing with **local LLM enrichment via Ollama (deepseek-coder:1.3b)** to provide deep code insights while maintaining data security.

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Neo4j 5.26+** (Community or Enterprise)
- **Ollama** with deepseek-coder:1.3b model
- **Git** for cloning the repository

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/darshan-e-zest/csharp-parser-creation.git
   cd csharp-parser-creation
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Neo4j**
   ```bash
   # Using Docker (recommended)
   docker run -d \
     --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:5.26
   ```

4. **Install and configure Ollama**
   ```bash
   # Install Ollama (macOS/Linux)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the deepseek-coder model
   ollama pull deepseek-coder:1.3b
   
   # Start Ollama service
   ollama serve
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Generate ANTLR parser**
   ```bash
   chmod +x scripts/generate_parser.sh
   ./scripts/generate_parser.sh
   ```

### Quick Test

```bash
# Test with sample C# code
python cli.py input_code/sample.cs

# Or use batch mode for directories
python cli.py --batch input_code/
```

## 📁 Project Structure

```
csharp-parser-creation/
├── 📂 api/                     # FastAPI web service
│   ├── main.py                 # API entry point
│   └── routers/                # API route handlers
│       ├── process_code.py     # Single file processing
│       └── trigger_etl.py      # Batch ETL pipeline
├── 📂 docs/                    # Documentation
│   └── architecture.md         # Detailed system architecture
├── 📂 grammar/                 # ANTLR grammar files
│   └── CSharp.g4              # C# language grammar
├── 📂 generated/               # Auto-generated ANTLR parsers
├── 📂 input_code/              # Input C# source files
├── 📂 raw/                     # Extracted raw files (temporary)
├── 📂 staging/                 # Intermediate processing files
│   └── ast/                    # Parsed AST JSON files
├── 📂 curated/                 # Final enriched output
├── 📂 archive/                 # Archived processed files
├── 📂 logs/                    # System logs
│   ├── etl/                    # ETL pipeline logs
│   └── llm_raw/               # Raw LLM request/response logs
├── 📂 pipeline/                # Core processing modules
│   ├── cs_parser.py           # ANTLR-based C# parser
│   ├── enrich.py              # LLM enrichment with chunked strategy
│   ├── insert_graph.py        # Neo4j graph ingestion
│   ├── models.py              # Neo4j schema definitions
│   ├── extract.py             # File extraction utilities
│   ├── archive.py             # Post-processing archival
│   └── run_etl.py             # Complete ETL orchestration
├── 📂 prompt_templates/        # LLM prompt engineering
├── 📂 scripts/                # Utility scripts
├── 📂 tests/                  # Comprehensive test suite
├── cli.py                     # Command-line interface
├── requirements.txt           # Python dependencies
└── .env.example              # Environment configuration template
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# Neo4j Configuration
NEO4J_BOLT_URL=localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
LLM_MODEL=deepseek-coder:1.3b

# Optional: Enable mock mode for testing without LLM
MOCK_ENRICHMENT=false

# Logging
LOG_LEVEL=INFO
```

### Neo4j Database Setup

The system automatically creates the following node types and relationships:

**Node Types:**
- `Project` - Top-level project container
- `Module` - Package/namespace containers
- `File` - Individual source files
- `CodeEntity` - All code constructs (classes, methods, properties, etc.)

**Relationships:**
- `HAS_MODULE` - Project contains modules
- `HAS_FILE` - Module contains files
- `HAS_ENTITY` - File contains code entities
- `CONTAINS` - Hierarchical containment (class contains methods)
- `DEPENDS_ON` - Dependency relationships
- `IMPLEMENTS` - Interface implementation
- `INHERITS_FROM` - Class inheritance
- `RETURNS` - Method return types
- `HAS_PARAMETER` - Method parameters

## 🚀 Usage

### Command Line Interface (CLI)

#### Single File Processing
```bash
# Process a single C# file
python cli.py path/to/MyClass.cs

# With verbose output
python cli.py -v path/to/MyClass.cs
```

#### Batch Processing (Recommended)
```bash
# Process entire directory
python cli.py --batch input_code/

# Process ZIP archive
python cli.py --batch csharp-project.zip

# Skip specific phases
python cli.py --batch input_code/ --skip enrich load

# Custom output directory
python cli.py --batch input_code/ --output-base /custom/path
```

#### ETL Pipeline Phases

The batch mode runs a complete ETL pipeline:

1. **Extract** - Unzip/copy source files to `raw/`
2. **Parse** - Convert C# to AST JSON in `staging/ast/`
3. **Enrich** - Add LLM metadata and save to `curated/`
4. **Load** - Insert into Neo4j graph database
5. **Archive** - Move processed files to `archive/`

### REST API

Start the FastAPI server:
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### API Endpoints

**Health Check**
```bash
curl http://localhost:8000/
```

**Process Single File**
```bash
curl -X POST "http://localhost:8000/api/process" \
  -H "Content-Type: application/json" \
  -d '{"file_path": "/absolute/path/to/file.cs"}'
```

**Trigger ETL Pipeline**
```bash
curl -X POST "http://localhost:8000/api/trigger-etl" \
  -H "Content-Type: application/json" \
  -d '{
    "input_path": "/path/to/csharp/project",
    "skip_phases": ["archive"]
  }'
```

### Python API

```python
from pipeline.run_etl import run_etl_pipeline

# Run complete ETL pipeline
result = run_etl_pipeline(
    input_path="path/to/csharp/code",
    skip_phases=["archive"]
)

print(f"Status: {result['status']}")
print(f"Files processed: {result['files_processed']}")
```

## 🧠 LLM Integration

### Local AI with Ollama

The system uses **Ollama with deepseek-coder:1.3b** for secure, local code analysis:

**Benefits:**
- **Data Security**: All analysis happens locally
- **No API Costs**: One-time setup, no per-token charges
- **Offline Operation**: Works without internet connectivity
- **Compliance Ready**: Meets enterprise security requirements

### Chunked Enrichment Strategy

To improve reliability and reduce JSON parsing errors, the system uses a chunked approach:

1. **Class-Level Analysis**: Each class analyzed separately for architectural patterns
2. **Method-Level Analysis**: Individual methods analyzed for functionality
3. **Composition**: Results merged into cohesive enriched output
4. **Fallback Handling**: Mock enrichment when LLM unavailable

### Model Requirements

- **Minimum**: 8GB RAM, 4 CPU cores
- **Recommended**: 16GB RAM, 8 CPU cores
- **Storage**: 2GB for model files

## 📊 Output Formats

### AST JSON (staging/ast/)
```json
[
  {
    "type": "Class",
    "name": "CustomerController",
    "startLine": 3,
    "modifiers": ["public"],
    "body": [
      {
        "type": "Method",
        "name": "GetCustomers",
        "startLine": 5,
        "returnType": "IActionResult",
        "parameters": []
      }
    ]
  }
]
```

### Enriched JSON (curated/)
```json
{
  "ast": [...],
  "summary": "Customer management API controller",
  "dependencies": ["CustomerService", "IActionResult"],
  "tags": ["controller", "api", "web"],
  "processing_info": {
    "classes_processed": 1,
    "methods_processed": 3,
    "strategy": "chunked"
  }
}
```

### Neo4j Graph Queries

```cypher
// Find all API controllers
MATCH (c:CodeEntity {type: "Class"})
WHERE c.name CONTAINS "Controller"
RETURN c.name, c.summary

// Find method dependencies
MATCH (m:CodeEntity {type: "Method"})-[:DEPENDS_ON]->(d:CodeEntity)
RETURN m.name, collect(d.name) as dependencies

// Find class hierarchies
MATCH (c:CodeEntity)-[:INHERITS_FROM]->(parent:CodeEntity)
RETURN c.name, parent.name
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_cs_parser.py -v
pytest tests/test_enrich.py -v
pytest tests/test_insert_graph.py -v
pytest tests/test_api.py -v

# Run with coverage
pytest tests/ --cov=pipeline --cov-report=html
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Cross-component functionality
- **API Tests**: REST endpoint validation
- **ETL Tests**: End-to-end pipeline testing

### Mock Testing

Enable mock mode for testing without LLM:
```bash
export MOCK_ENRICHMENT=true
python cli.py input_code/sample.cs
```

## 🔍 Monitoring and Logging

### Log Files

- **Pipeline Logs**: `pipeline_run.log` - General application logs
- **ETL Logs**: `logs/etl/etl_run_*.json` - ETL execution statistics
- **LLM Logs**: `logs/llm_raw/llm_response_*.json` - Raw LLM interactions

### View Logs

```bash
# View recent ETL runs
python logs/logger.py etl --limit 5

# View LLM interactions
python logs/logger.py llm --limit 10

# Filter LLM logs by run ID
python logs/logger.py llm --run-id 20231201_143022
```

### Monitoring Queries

```cypher
// Monitor processing statistics
MATCH (f:File)
RETURN count(f) as total_files

MATCH (c:CodeEntity)
RETURN c.type, count(c) as count
ORDER BY count DESC

// Find processing errors
MATCH (n:CodeEntity)
WHERE n.tags CONTAINS "error"
RETURN n.name, n.summary
```

## 📈 Performance Optimization

### Chunked Processing Benefits

- **Parallel Processing**: Classes and methods processed concurrently
- **Improved Reliability**: Smaller prompts reduce LLM errors
- **Better Resource Usage**: Focused context improves quality
- **Selective Processing**: Skip enrichment for certain types

### Hardware Scaling

**Vertical Scaling:**
- Upgrade to larger models (deepseek-coder:6.7b)
- Increase RAM for larger codebases
- Use SSD storage for faster file I/O

**Horizontal Scaling:**
- Multiple Ollama instances on different ports
- Distributed processing across machines
- Load balancing between LLM instances

## 🔒 Security and Compliance

### Data Security Features

- **Local Processing**: No external API calls
- **Air-Gapped Operation**: Works in isolated environments
- **Secure Storage**: Encrypted Neo4j connections
- **Access Control**: Configurable authentication

### Enterprise Compliance

- **Data Sovereignty**: Code never leaves local infrastructure
- **Audit Trails**: Complete logging of all operations
- **GDPR Ready**: No personal data transmitted externally
- **SOC 2 Compatible**: Secure configuration options

## 🚧 Troubleshooting

### Common Issues

**1. ANTLR Parser Generation Fails**
```bash
# Ensure Java is installed
java -version

# Regenerate parser
rm -rf generated/
./scripts/generate_parser.sh
```

**2. Neo4j Connection Issues**
```bash
# Check Neo4j status
docker ps | grep neo4j

# Test connection
python -c "from pipeline.models import CodeEntity; print('Connected!')"
```

**3. Ollama Model Not Found**
```bash
# List available models
ollama list

# Pull required model
ollama pull deepseek-coder:1.3b

# Check service status
curl http://localhost:11434/api/tags
```

**4. Memory Issues with Large Codebases**
```bash
# Use selective processing
python cli.py --batch large_project/ --skip enrich

# Or process in smaller chunks
find input_code/ -name "*.cs" | head -50 | xargs python cli.py
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python cli.py -v input_code/

# Enable mock mode for testing
export MOCK_ENRICHMENT=true
python cli.py input_code/
```

## 🤝 Contributing

### Development Setup

1. **Fork and clone the repository**
2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```
3. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```
4. **Run tests before changes**
   ```bash
   pytest tests/ -v
   ```

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **Documentation**: Use Google-style docstrings
- **Testing**: Maintain >80% test coverage
- **Logging**: Use centralized logger module

### Pull Request Process

1. Create feature branch from `main`
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass
5. Submit PR with detailed description

## 📚 Additional Resources

### Documentation

- **[Architecture Guide](docs/architecture.md)** - Detailed system design
- **[API Reference](http://localhost:8000/docs)** - Interactive API docs (when server running)
- **[Neo4j Graph Schema](docs/graph-schema.md)** - Database structure

### Related Technologies

- **[ANTLR](https://www.antlr.org/)** - Parser generator framework
- **[Neo4j](https://neo4j.com/docs/)** - Graph database documentation
- **[Ollama](https://ollama.ai/)** - Local LLM runtime
- **[FastAPI](https://fastapi.tiangolo.com/)** - Python web framework
- **[deepseek-coder](https://github.com/deepseek-ai/deepseek-coder)** - Code-specialized LLM

### Community

- **Issues**: Report bugs and feature requests on GitHub
- **Discussions**: Join community discussions
- **Discord**: Real-time chat support [Link]

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ANTLR Community** for the excellent C# grammar
- **Neo4j Team** for the powerful graph database
- **Ollama Project** for local LLM infrastructure
- **deepseek-ai** for the specialized code analysis model

---

## 📊 Project Status

- ✅ **Core Pipeline**: Stable and production-ready
- ✅ **Local LLM Integration**: Fully implemented with Ollama
- ✅ **Chunked Enrichment**: Enhanced reliability and performance
- ✅ **REST API**: Complete with comprehensive endpoints
- ✅ **Batch Processing**: ETL pipeline with full lifecycle management
- ✅ **Testing Suite**: Comprehensive unit and integration tests
- 🚧 **Performance Optimization**: Ongoing improvements
- 🚧 **Documentation**: Continuous updates and examples

---

**Built with ❤️ for code analysis and graph exploration**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/darshan-e-zest/csharp-parser-creation).
