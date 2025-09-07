# C# → Neo4j Code Graph Extractor: Usage Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
   - [Mac OS](#mac-os)
   - [Linux](#linux)
   - [Windows](#windows)
3. [Configuration](#configuration)
   - [LLM Setup with Ollama](#llm-setup-with-ollama)
   - [Environment Variables](#environment-variables)
4. [Basic Usage](#basic-usage)
   - [CLI Usage](#cli-usage)
   - [API Usage](#api-usage)
5. [Advanced Usage](#advanced-usage)
   - [LLM Provider Customization](#llm-provider-customization)
   - [Working with Large Codebases](#working-with-large-codebases)
6. [Troubleshooting](#troubleshooting)
7. [Examples](#examples)

## Prerequisites

Before using this tool, ensure you have the following installed:

- Python 3.10 or higher
- Java 17 or higher (required for ANTLR)
- Neo4j 5.x (local instance or remote access)
- Git (for cloning the repository)
- Ollama (for local LLM - CodeLlama model)

## Installation

### Mac OS

1. **Clone the Repository:**

```bash
git clone https://github.com/yourusername/csharp-parser-creation.git
cd csharp-parser-creation
```

2. **Set Up Python Environment:**

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Install Java 17:**

```bash
# Using Homebrew
brew install openjdk@17

# Verify installation
java --version
```

4. **Install Neo4j:**

```bash
# Using Homebrew
brew install neo4j

# Start Neo4j
brew services start neo4j

# Access Neo4j Browser at http://localhost:7474
# Default credentials: neo4j/neo4j (you'll be prompted to change on first login)
```

5. **Install Ollama:**

```bash
# Using Homebrew
brew install ollama

# Start Ollama service
ollama serve

# In a new terminal, pull the CodeLlama model
ollama pull codellama
```

6. **Generate ANTLR Parser:**

```bash
# Make the script executable
chmod +x scripts/generate_parser.sh

# Run the generator script
./scripts/generate_parser.sh
```

### Linux

1. **Clone the Repository:**

```bash
git clone https://github.com/yourusername/csharp-parser-creation.git
cd csharp-parser-creation
```

2. **Set Up Python Environment:**

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. **Install Java 17:**

```bash
# For Ubuntu/Debian
sudo apt install openjdk-17-jdk

# For Fedora/CentOS
sudo dnf install java-17-openjdk-devel

# Verify installation
java --version
```

4. **Install Neo4j:**

```bash
# Follow instructions at https://neo4j.com/docs/operations-manual/current/installation/linux/

# Start Neo4j
sudo systemctl start neo4j

# Access Neo4j Browser at http://localhost:7474
# Default credentials: neo4j/neo4j (you'll be prompted to change on first login)
```

5. **Install Ollama:**

```bash
# Download and install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve

# In a new terminal, pull the CodeLlama model
ollama pull codellama
```

6. **Generate ANTLR Parser:**

```bash
# Make the script executable
chmod +x scripts/generate_parser.sh

# Run the generator script
./scripts/generate_parser.sh
```

### Windows

1. **Clone the Repository:**

```powershell
git clone https://github.com/yourusername/csharp-parser-creation.git
cd csharp-parser-creation
```

2. **Set Up Python Environment:**

```powershell
# Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. **Install Java 17:**
   - Download the installer from [Oracle](https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html) or [AdoptOpenJDK](https://adoptium.net/)
   - Run the installer and follow the instructions
   - Verify with `java --version` in a new command prompt

4. **Install Neo4j:**
   - Download the installer from [Neo4j Download Center](https://neo4j.com/download-center/)
   - Run the installer and follow the instructions
   - Start Neo4j via Neo4j Desktop or as a service
   - Access Neo4j Browser at http://localhost:7474
   - Default credentials: neo4j/neo4j (you'll be prompted to change on first login)

5. **Install Ollama:**
   - Download the Windows installer from [Ollama's website](https://ollama.com/download)
   - Run the installer and follow the instructions
   - Open a PowerShell window and run:

```powershell
# Pull the CodeLlama model
ollama pull codellama
```

6. **Generate ANTLR Parser:**
   - Use Git Bash or WSL to run the script:

```bash
# Make the script executable
chmod +x scripts/generate_parser.sh

# Run the generator script
./scripts/generate_parser.sh
```

## Configuration

### LLM Setup with Ollama

This project currently uses CodeLlama via Ollama for LLM-based code enrichment. Ollama runs locally on your machine, providing privacy and reduced latency.

1. **Verify Ollama Service:**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags
```

2. **Test CodeLlama Model:**

```bash
# Simple test of the model
ollama run codellama "Explain what this code does: function add(a, b) { return a + b; }"
```

### Environment Variables

Copy the template environment file and configure it for your environment:

```bash
cp .env.template .env
```

Edit `.env` with your preferred text editor and update the following values:

```ini
# LLM provider configuration
LLM_PROVIDER=ollama            # Current default is Ollama
LLM_MODEL=codellama            # Using CodeLlama model
OLLAMA_BASE_URL=http://localhost:11434

# Neo4j credentials
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_BOLT_URL=bolt://localhost:7687

# ANTLR CONFIG (Optional)
ANTLR_JAR_PATH=./antlr/antlr-4.13.1-complete.jar
ANTLR_GRAMMAR_DIR=./antlr/csharp/
ANTLR_OUTPUT_DIR=./antlr/generated/
```

## Basic Usage

There are two ways to use the tool:

1. Command-line interface (CLI)
2. HTTP API (FastAPI application)

### CLI Usage

The CLI tool processes a single C# file through the complete pipeline:

```bash
# Make sure you're in the project root directory with activated virtual environment
# On Mac/Linux:
python cli.py path/to/your/file.cs

# On Windows:
python cli.py path\to\your\file.cs
```

This will:
1. Parse the C# file into AST nodes
2. Serialize the AST to JSON in `parsed_output/`
3. Enrich the AST with CodeLlama-generated insights via Ollama
4. Store the enriched data in `enriched_output/`
5. Insert the data into Neo4j as a graph

### API Usage

#### Starting the API Server

```bash
# Navigate to the API directory
cd api

# For Mac/Linux:
# Start the FastAPI server (development mode)
uvicorn main:app --reload

# For Windows:
# Start the FastAPI server (development mode)
uvicorn main:app --reload

# For production on any platform, use:
# uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000/`.

#### API Endpoints

| Endpoint      | Method | Description                | Request Body                    |
|---------------|--------|----------------------------|--------------------------------|
| `/`           | GET    | Health check               | None                           |
| `/api/process`| POST   | Process a C# file          | `{"file_path": "/path/to.cs"}` |

#### Example API Request

Using curl (Mac/Linux):

```bash
curl -X POST "http://localhost:8000/api/process" \
     -H "Content-Type: application/json" \
     -d '{"file_path": "/absolute/path/to/your/file.cs"}'
```

Using curl (Windows PowerShell):

```powershell
curl.exe -X POST "http://localhost:8000/api/process" `
     -H "Content-Type: application/json" `
     -d '{\"file_path\": \"C:\\path\\to\\your\\file.cs\"}'
```

Using Python requests (any platform):

```python
import requests

response = requests.post(
    "http://localhost:8000/api/process",
    json={"file_path": "/absolute/path/to/your/file.cs"}  # Use proper Windows path if on Windows
)
print(response.json())
```

## Advanced Usage

### LLM Provider Customization

The system is designed to be LLM provider agnostic. You can easily switch between different providers by modifying the `.env` file:

#### Using Ollama (Default)
```ini
LLM_PROVIDER=ollama
LLM_MODEL=codellama
OLLAMA_BASE_URL=http://localhost:11434
```

#### Using OpenAI
```ini
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=your_api_key_here
```

#### Using Groq
```ini
LLM_PROVIDER=groq
LLM_MODEL=llama3-8b-8192
GROQ_API_KEY=your_api_key_here
```

#### Using HuggingFace
```ini
LLM_PROVIDER=huggingface
LLM_MODEL=mistralai/Mixtral-8x7B-Instruct-v0.1
HUGGINGFACE_API_KEY=your_api_key_here
```

### Working with Large Codebases

For large codebases with many files, process them in batches:

#### Mac/Linux:

```bash
# Example shell script for processing multiple files
for file in path/to/codebase/*.cs; do
    python cli.py "$file"
    # Optional: add sleep to limit API rate
    sleep 1
done
```

#### Windows:

```powershell
# PowerShell script for processing multiple files
$files = Get-ChildItem -Path "path\to\codebase\*.cs"
foreach ($file in $files) {
    python cli.py $file.FullName
    # Optional: add sleep to limit API rate
    Start-Sleep -Seconds 1
}
```

### Customizing LLM Prompts

Edit `prompt_templates/csharp_enrich_prompt.txt` to customize how the LLM enriches your code. The template uses a placeholder `{{AST_JSON}}` that will be replaced with your AST data.

## Troubleshooting

### Common Issues

1. **Parser generation fails**:
   - Ensure Java 17+ is installed (`java --version`)
   - Verify ANTLR JAR exists in scripts/ directory
   - On Windows, try using Git Bash or WSL to run the script

2. **Ollama connectivity issues**:
   - Verify Ollama is running: `curl http://localhost:11434/api/tags`
   - Check if CodeLlama model is downloaded: `ollama list`
   - If not downloaded, run: `ollama pull codellama`

3. **Neo4j connection fails**:
   - Ensure Neo4j is running:
     - Mac: `brew services list`
     - Linux: `sudo systemctl status neo4j`
     - Windows: Check Neo4j Desktop or Services
   - Verify credentials in .env file
   - Check network connectivity to Neo4j server
   - For Windows, ensure the URI format is correct in .env file

### Logs

Check the following for detailed error logs:

- FastAPI logs in the terminal window where you started the server
- Python exceptions printed to console during CLI usage
- For Ollama issues, check Ollama service logs:
  - Mac/Linux: `journalctl -u ollama`
  - Windows: Check the Event Viewer

## Examples

### Example 1: Processing a Simple C# Class

#### Mac/Linux:

```bash
# Place example file in input_code/
cat << 'EOF' > input_code/SimpleClass.cs
namespace ExampleApp {
    public class SimpleClass {
        public string Name { get; set; }
        
        public void DoWork() {
            // Method implementation
        }
    }
}
EOF

# Process the file with CLI
python cli.py input_code/SimpleClass.cs

# Check Neo4j browser for results
```

#### Windows:

```powershell
# Place example file in input_code/
$code = @"
namespace ExampleApp {
    public class SimpleClass {
        public string Name { get; set; }
        
        public void DoWork() {
            // Method implementation
        }
    }
}
"@
Set-Content -Path "input_code\SimpleClass.cs" -Value $code

# Process the file with CLI
python cli.py input_code\SimpleClass.cs

# Check Neo4j browser for results
```

### Example 2: Visualizing Dependencies

After processing multiple C# files, use Neo4j Browser to run:

```cypher
MATCH path = (c:CodeEntity {type: 'Class'})-[:DEPENDS_ON*1..2]->(d:CodeEntity)
RETURN path LIMIT 25
```

This will show a visualization of class dependencies up to 2 levels deep.
