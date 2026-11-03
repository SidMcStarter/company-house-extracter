from dotenv import load_dotenv
import os
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_core.documents import Document
from langchain_ollama.llms import OllamaLLM
import asyncio
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

NEO4J_URI = "neo4j://127.0.0.1:7687"
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Define the LLM
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0,
)

graph_transformer = LLMGraphTransformer(llm=llm)

# Main async function
async def main():
    with open("documents/AA_MzA0MTYzNDYxN2FkaXF6a2N4-pages.txt") as f:
        text = f.read()

    pages = text.split("--- End of Page")
    documents = [Document(page_content=page.strip()) for page in pages if page.strip()]
    print(f"Loaded {len(documents)} documents from text.")
    documents = documents[:2]  # Limit to first 2 documents for testing
    graph_documents = await graph_transformer.aconvert_to_graph_documents(documents)
    print(graph_documents)

# Run the async main
if __name__ == "__main__":
    asyncio.run(main())
