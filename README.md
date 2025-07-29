*THE PROJECT IS STILL UNDERDEVELOPMENT*


# Code-Nebula
Turn legacy C# code into smart, searchable graphs using Neo4j and AI — with easy setup and local privacy.

This tool helps you:
Understand large old C# projects
See how different parts of your code connect (classes, methods, inheritance, etc.)
Use AI (locally) to summarize and explain your code
Store all this in a visual graph database: Neo4j


### 🚀 **What You’ll Need**

Before you start, make sure you have these installed:

Python : 3.10 or higher	           
Neo4j  : 5.26+	 
Ollama + DeepSeek Coder	Model : deepseek-coder:1.3b 
Git	Latest	To download the project


### 🛠️ __Setup Guide__

1. Clone the Project
 ```bash
//Repo cloning link
```
2. Install Python Packages
```bash
  pip install -r requirements.txt
   //can change as per project development 
```
3. Start Neo4j (using Docker - easiest way)
```bash
  //Section will be filled after Docker setup
```
4. Install Ollama & the AI Model
```bash
   //Install Ollama
   //after ollama setup
   //Start the Ollama server
   //Download the model
```
5. Configure Your Environment
 ```bash
  Copy the config file and update values if needed:
  cp .env.example .env
```



### 🧪 __Try It Out__

🌐 Option A: CLI (Command Line)
  //after cli implementation 


🌐 Option B: Web API (Optional)
    Start the server:
    #after api integration 

Visit the docs:
👉 //docs folder
- **[Architecture Guide](docs/workflow.md)** - Detailed system design



### 🧠 **How It Works**

1. Extract: Reads .cs files from your input

2. Parse: Converts code into structured form (AST)

3. Enrich: AI explains the code

4. Store: Saves all the data into Neo4j as a graph



### 📊 **Output Examples**

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
💡 AI Enriched JSON

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


### 🕵️ **See Your Code as a Graph**

Once your code is processed, you can run queries like:

// Find all controllers
MATCH (c:CodeEntity {type: "Class"})
WHERE c.name CONTAINS "Controller"
RETURN c.name, c.summary
#sample cypher query


### 🧪 **Run Tests**
//to be updated


### 🔍 **Troubleshooting**

Problem	Fix
//to be updated


### 💬 **Questions or Want to Contribute?**

Open Issues

Join discussions or fork this project

PRs welcome! Just keep your code clean and tested.



### 🙌 **Thanks To**

Our college guide for project support 

And all contributors ❤️


