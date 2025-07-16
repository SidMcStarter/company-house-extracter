from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_neo4j import Neo4jGraph
import os

async def ingest_text_to_neo4j(
    text_file_path: str,
    neo4j_uri: str = os.getenv("NEO4J_URI"),
    neo4j_user: str = os.getenv("NEO4J_USER"),
    neo4j_password: str = os.getenv("NEO4J_PASSWORD"),
    llm_model: str = "gpt-4o-mini"
):
    # Read the document
    with open(text_file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Prepare LLM and transformer
    llm = ChatOpenAI(model=llm_model, temperature=0.0)
    graph_transformer = LLMGraphTransformer(llm=llm, node_properties=True)

    pages = text.split("--- End of Page")
    documents = [Document(page_content=page.strip()) for page in pages if page.strip()]

    # Convert to graph documents (async)
    graph_documents = await graph_transformer.aconvert_to_graph_documents(documents)

    # Store in Neo4j
    graph = Neo4jGraph(
        url=neo4j_uri,
        username=neo4j_user,
        password=neo4j_password,
        refresh_schema=True,
    )
    graph.add_graph_documents(graph_documents, baseEntityLabel=True, include_source=True)
    return graph_documents

if __name__ == "__main__":
    import asyncio
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    # Define the text file path
    text_file_path = "01471587/shortened-filings-text/123_MTM4MzYzMjUxYWRpcXprY3g.txt"

    # Run the ingestion
    asyncio.run(ingest_text_to_neo4j(text_file_path, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD))