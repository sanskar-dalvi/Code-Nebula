import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_BOLT_URL", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def insert_enriched_graph(enriched_ast):
    print("[Graph] Inserting into Neo4j...")

    with driver.session() as session:
        for node in enriched_ast:
            session.run(
                """
                MERGE (c:CodeEntity {name: $class_name, type: "Class"})
                MERGE (m:CodeEntity {name: $method_name, type: "Method"})
                MERGE (c)-[:HAS_METHOD]->(m)
                SET m.summary = $summary,
                    m.tags = $tags
                """,
                class_name=node.get("class"),
                method_name=node.get("method"),
                summary=node.get("summary"),
                tags=node.get("tags"),
            )
            print(f"[Graph] Inserted {node.get('class')}::{node.get('method')}")

    print("[Graph] Neo4j insertion complete.")
