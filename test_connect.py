from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def test_push():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        session.run(
            "MATCH (n) DETACH DELETE n"
        )
        session.run(
            "CREATE (player:Player {name: $name, age: $age, country: $country})",
            name="Siddharth", age=25, country="India"
    )
        session.run(
            "CREATE (player:Player {name: $name, age: $age, country: $country})",
            name="Alice", age=30, country="USA"
        )
        
        session.run(
            """
            MATCH (a:Player {name: $name1}), (b:Player {name: $name2})
            MERGE (a) - [:TEAMATES]-> (b)
            MERGE (b) - [:TEAMATES]-> (a)
            """,
            name1="Siddharth", name2="Alice"
        )
    driver.close()
    print("Test node created!")

if __name__ == "__main__":
    test_push()