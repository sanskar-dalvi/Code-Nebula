# Project Task List

## Project Goal

To build an automated pipeline that can parse C# source code, use an AI model to analyze and enrich the code's structure with summaries and tags, and load this interconnected data into a Neo4j graph database. The system will be controlled via a Command-Line Interface (CLI) and a REST API.

## Team & Responsibilities

| Name                | Role                          | Primary Responsibilities                                   |
| ------------------- | ----------------------------- | ---------------------------------------------------------- |
| **Sanskar Dalvi**   | Owner / AI & DB Lead          | All AI/LLM integration, Neo4j schema, and data ingestion.  |
| **Kshitij Landge**  | Infrastructure & Setup Lead   | Initial project setup, dependencies, and file handling.    |
| **Ganesh Muthal**   | Parsing Lead                  | All C# source code parsing logic using ANTLR.              |
| **Utkarsha Mahale** | API Lead                      | Development and testing of all FastAPI endpoints.          |
| **Rushikesh Chaudhari** | Orchestration & CI/CD Lead    | End-to-end pipeline orchestration, CLI, testing, and docs. |

---

## Phase 1: Project Foundation & Scaffolding

*   **Goal:** To create a complete, version-controlled project skeleton. This phase is critical for enabling parallel work.
*   **Lead:** **Kshitij Landge**
*   **Workflow:** Kshitij will complete all tasks in this phase and push them to the `main` branch. All other team members will wait for this to be complete before starting Phase 2.

| Task ID | Description & Definition of Done                                                                                                                                                                                                                                                        | Files to Create/Edit                                                                                                                                                           | Status      |
| :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :---------- |
| `P1.1`  | **Initialize Git Repository & Main Files**<br/>- Create the Git repo.<br/>- **Done when:** `.gitignore` excludes standard Python/IDE files, `requirements.txt` lists all key libraries (e.g., `fastapi`, `neomodel`), and `.env.template` contains placeholders for all secrets. | `README.md`, `.gitignore`, `requirements.txt`, `.env.template`                                                                                                                 | `☐ Pending` |
| `P1.2`  | **Create Project Directory Structure**<br/>- Create the full folder tree.<br/>- **Done when:** All specified directories exist, and Python packages (like `pipeline`) contain an empty `__init__.py`.                                                                                  | `api/`, `docs/`, `grammar/`, `input_code/`, `pipeline/`, `scripts/`, `tests/`                                                                                                  | `☐ Pending` |
| `P1.3`  | **Scaffold All Module and Script Stubs**<br/>- Create empty files with placeholder content.<br/>- **Done when:** Each file exists with a minimal valid structure (e.g., `def main(): pass` or `#!/usr/bin/env bash`), reserving it for its owner. | `cli.py`, `pipeline/cs_parser.py`, `pipeline/enrich.py`, `pipeline/insert_graph.py`, `pipeline/models.py`, `api/main.py`, `api/routers/process_code.py`, `scripts/*`                | `☐ Pending` |
| `P1.4`  | **Scaffold All Test File Stubs**<br/>- Create empty test files.<br/>- **Done when:** Each test file contains `import pytest` and a single passing test (`def test_stub(): assert True`), confirming the test runner is functional.               | `tests/test_cs_parser.py`, `tests/test_enrich.py`, `tests/test_insert_graph.py`, `tests/test_api.py`, `tests/test_cli.py`                                                          | `☐ Pending` |
| `P1.5`  | **Commit & Push Foundation**<br/>- Commit all of the above to the `main` branch.<br/>- **Done when:** The team can clone a repo that is ready for Phase 2 development.                                                                                                                   | -                                                                                                                                                                              | `☐ Pending` |

---

## Phase 2: Core Component Development (Parallel Work)

*   **Goal:** For each team member to independently implement the core logic of their assigned modules.
*   **Workflow:** Everyone works in parallel, editing **only their assigned files**.

### **Ganesh Muthal (Parsing Logic)**

| Task ID | Description & Definition of Done                                                                                                                                                                                                                             | Files to Edit/Create                               | Status      |
| :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------- | :---------- |
| `P2.1`  | **Implement C# Parser**<br/>- Add C# `.g4` files to `grammar/`.<br/>- Run the generation script.<br/>- In `cs_parser.py`, create an `ASTCollector` class that inherits from the generated ANTLR `Visitor` to extract class and method names.<br/>- **Done when:** The `parse_cs_file` function can take a file path and return a list of dicts representing the AST. | `pipeline/cs_parser.py`, `grammar/`                | `☐ Pending` |
| `P2.2`  | **Write Parser Tests**<br/>- Add a sample `SampleController.cs` to `input_code/`.<br/>- Write a test in `tests/test_cs_parser.py` that calls the parser with the sample file and asserts that the returned list contains the expected class/method names. <br/>- **Done when:** The test passes, proving the parser works as expected. | `tests/test_cs_parser.py`, `input_code/`           | `☐ Pending` |

### **Sanskar Dalvi (AI & Database Logic)**

| Task ID | Description & Definition of Done                                                                                                                                                                                                                              | Files to Edit/Create                                     | Status      |
| :------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------- | :---------- |
| `P2.3`  | **Implement Neo4j Data Models**<br/>- In `pipeline/models.py`, define a `CodeEntity(StructuredNode)` with `StringProperty`, `JSONProperty`, and `RelationshipTo` fields. <br/>- Configure the database connection using variables from `.env`. <br/>- **Done when:** The model schema accurately represents the code entities and their relationships. | `pipeline/models.py`                                     | `☐ Pending` |
| `P2.4`  | **Implement AI Enrichment Logic**<br/>- Create a prompt in `prompt_templates/`.<br/>- In `pipeline/enrich.py`, write functions to build the prompt with AST data, call the LLM API via `requests`, and parse the JSON response.<br/>- **Done when:** The `enrich_ast` function can take an AST and return a dictionary with the LLM's summary, tags, etc. | `pipeline/enrich.py`, `prompt_templates/`                | `☐ Pending` |
| `P2.5`  | **Implement Graph Ingestion Logic**<br/>- In `pipeline/insert_graph.py`, write a function to iterate through the enriched data.<br/>- Use `CodeEntity.nodes.get_or_none()` to check for existing nodes before creating new ones with `.save()`.<br/>- Connect nodes using `.connect()`. <br/>- **Done when:** The function can populate a Neo4j database from an enriched data structure. | `pipeline/insert_graph.py`                               | `☐ Pending` |
| `P2.6`  | **Write AI & DB Unit Tests**<br/>- For `test_enrich.py`, use `unittest.mock.patch` to simulate the LLM API response.<br/>- For `test_insert_graph.py`, test against a local/Dockerized Neo4j instance. <br/>- **Done when:** Both tests pass, validating the logic without making real API calls or relying on pre-existing data. | `tests/test_enrich.py`, `tests/test_insert_graph.py`     | `☐ Pending` |

### **Utkarsha Mahale (API Development)**

| Task ID | Description & Definition of Done                                                                                                                                                                                                                                      | Files to Edit/Create                    | Status      |
| :------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------- | :---------- |
| `P2.7`  | **Implement API Endpoint**<br/>- In `api/routers/process_code.py`, create an `APIRouter` and define a `POST /process` endpoint that accepts a filepath via a Pydantic model. <br/>- The function body can be a placeholder for now. <br/>- **Done when:** The endpoint is defined with the correct request model. | `api/routers/process_code.py`           | `☐ Pending` |
| `P2.8`  | **Configure Main API App**<br/>- In `api/main.py`, import the router from `process_code.py` and register it with the main FastAPI app using `app.include_router()`.<br/>- **Done when:** The API app is aware of the new endpoint.                                                  | `api/main.py`                           | `☐ Pending` |
| `P2.9`  | **Write API Stub Tests**<br/>- In `tests/test_api.py`, use FastAPI's `TestClient` to send a request to the `/process` endpoint.<br/>- **Done when:** The test confirms the endpoint exists and returns a success status code (e.g., 200).                                 | `tests/test_api.py`                     | `☐ Pending` |

### **Rushikesh Chaudhari (CLI & Docs)**

| Task ID | Description & Definition of Done                                                                                                                                                                                          | Files to Edit/Create                             | Status      |
| :------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :----------------------------------------------- | :---------- |
| `P2.10` | **Implement CLI Structure**<br/>- In `cli.py`, use the `argparse` module to define a command-line argument that accepts an input file path. <br/>- The main function will be a placeholder for now. <br/>- **Done when:** The script can be run from the command line with a file path argument without error. | `cli.py`                                         | `☐ Pending` |
| `P2.11` | **Write Initial Documentation**<br/>- In `docs/architecture.md`, create sections for each pipeline step.<br/>- In `docs/usage.md`, write the initial setup and "How to Run" instructions. <br/>- **Done when:** The documents have a clear structure outlining the project's design and intended use. | `docs/architecture.md`, `docs/usage.md`          | `☐ Pending` |
| `P2.12` | **Write CLI Stub Tests**<br/>- In `tests/test_cli.py`, use Python's `subprocess` module to run the CLI script with arguments. <br/>- **Done when:** The test asserts that the script exits with a success code (0).                                                   | `tests/test_cli.py`                              | `☐ Pending` |

---

## Phase 3: Integration and End-to-End Workflow

*   **Goal:** To connect all the independent modules into a single, functioning pipeline.
*   **Workflow:** The integrators (Rushikesh & Utkarsha) will modify their respective files (`cli.py` & `api/...`) to call the other pipeline modules. Other team members will be on standby to make adjustments to their modules if needed.

| Task ID | Description & Definition of Done                                                                                                                                                                                          | Responsible               | Files to Edit                      | Status      |
| :------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------ | :--------------------------------- | :---------- |
| `P3.1`  | **Integrate Pipeline in CLI**<br/>- In `cli.py`, import and call the functions from `cs_parser`, `enrich`, and `insert_graph` in sequence. <br/>- **Done when:** Running `python cli.py <path>` executes the full parse -> enrich -> ingest workflow. | Rushikesh Chaudhari       | `cli.py`                           | `☐ Pending` |
| `P3.2`  | **Integrate Pipeline in API**<br/>- In `api/routers/process_code.py`, do the same integration as the CLI within the `POST /process` endpoint. <br/>- **Done when:** Sending a POST request to the API executes the full workflow and returns a success message. | Utkarsha Mahale           | `api/routers/process_code.py`      | `☐ Pending` |
| `P3.3`  | **Write End-to-End Integration Tests**<br/>- Upgrade the API/CLI tests. After calling the endpoint/script, the test should connect to the test DB and run a Cypher query to assert that the expected nodes/relationships were created.<br/>- **Done when:** Tests prove the entire pipeline works from start to finish. | Rushikesh & Utkarsha      | `tests/test_cli.py`, `tests/test_api.py` | `☐ Pending` |
| `P3.4`  | **Refine DB Logic for Idempotency**<br/>- Ensure `insert_graph.py` uses `get_or_none` or a Cypher `MERGE` statement so that running the pipeline on the same file twice does not create duplicate data. <br/>- **Done when:** The pipeline is safely re-runnable. | Sanskar Dalvi             | `pipeline/insert_graph.py`, `pipeline/models.py` | `☐ Pending` |

---

## Phase 4: Batch Processing and Final Polish

*   **Goal:** To extend the pipeline to handle entire directories/ZIP files and complete all documentation.
*   **Workflow:** Team members will create or extend their modules to support batch operations.

| Task ID | Description & Definition of Done                                                                                                                                                                                                   | Responsible         | Files to Create/Edit                                  | Status      |
| :------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------ | :---------------------------------------------------- | :---------- |
| `P4.1`  | **Implement File Extraction Logic**<br/>- Create `pipeline/file_handler.py`. Write a function that accepts a path and, using `zipfile` or `pathlib`, returns a list of all `.cs` files to process. <br/>- **Done when:** The function can correctly discover files in both a directory and a ZIP archive. | Kshitij Landge      | `pipeline/file_handler.py`, `tests/test_file_handler.py` | `☐ Pending` |
| `P4.2`  | **Update Parser for Batch Mode**<br/>- Refactor `cs_parser.py` to accept a list of file paths and return a data structure that maps each AST node back to its source file. <br/>- **Done when:** The parser can process multiple files in one call. | Ganesh Muthal       | `pipeline/cs_parser.py`                               | `☐ Pending` |
| `P4.3`  | **Update DB for Cross-File Linking**<br/>- Update the `uid` in `models.py` to be a composite key (e.g., `f"{filepath}:{type}:{name}"`) to guarantee project-wide uniqueness.<br/>- Update `insert_graph.py` to create `DEPENDS_ON` relationships between nodes from different files. <br/>- **Done when:** The graph can represent the entire codebase, not just single files. | Sanskar Dalvi       | `pipeline/models.py`, `pipeline/insert_graph.py`      | `☐ Pending` |
| `P4.4`  | **Update CLI for Batch Mode**<br/>- Modify `cli.py` to accept a directory/ZIP path. Use the new `file_handler` and orchestrate the batch processing loop. <br/>- **Done when:** The CLI can process an entire project at once. | Rushikesh Chaudhari | `cli.py`                                              | `☐ Pending` |
| `P4.5`  | **Update API for Batch Mode**<br/>- Add a new `POST /process-batch` endpoint to the API that handles batch processing. <br/>- **Done when:** The API can trigger the processing of an entire project. | Utkarsha Mahale     | `api/routers/process_code.py`                         | `☐ Pending` |
| `P4.6`  | **Finalize All User Documentation**<br/>- Perform a final review and update of `README.md` and `docs/` to include instructions for batch processing and reflect the final architecture. <br/>- **Done when:** A new developer could understand and use the project from the documentation alone. | Rushikesh Chaudhari | `README.md`, `docs/`                                  | `☐ Pending` |
