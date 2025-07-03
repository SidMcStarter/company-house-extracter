from neo4j import GraphDatabase
from dotenv import load_dotenv
from get_codes import get_codes
import os

# Load environment variables
load_dotenv()

# Neo4j connection details
NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

def put_codes(codes):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        for code in codes:
            session.run (
                "MERGE (code: Filing {code: $code})",
                code=code
            )
    driver.close()
    
if __name__ == "__main__":
    codes = get_codes("01471587/filings/")
    put_codes(codes)  # Put the codes into the graph database
