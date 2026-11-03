import os
import json
import pandas as pd
from dotenv import load_dotenv

from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

def setup_chat_qa(vectorstore, openai_api_key=None):
    """
    Set up a conversational QA system using ChatGPT and the given vectorstore.
    """
    openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

    chat_model = ChatOpenAI(
        temperature=0.1,
        openai_api_key=openai_api_key,
        model="gpt-4o-mini"
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )

    return ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        memory=memory,
        return_source_documents=True
    )

def build_document_from_chunk(chunk):
    """
    Convert a chunk into a LangChain Document with metadata.
    """
    metadata = {
        "chunk_id": chunk.get("chunk_id", ""),
        "chunk_type": chunk.get("chunk_type", "")
    }

    if grounding := chunk.get("grounding"):
        for g in grounding:
            if "box" in g:
                box = g["box"]
                metadata.update({
                    "page": g.get("page", 0),
                    "position": f"l={box.get('l', 0):.2f}, t={box.get('t', 0):.2f}, r={box.get('r', 0):.2f}, b={box.get('b', 0):.2f}"
                })
                break

    return Document(page_content=chunk["text"], metadata=metadata), {
        **metadata,
        "page_content": chunk["text"]
    }

def generate_persist_path(json_path, collection_name):
    base_name = collection_name or os.path.basename(json_path).split('.')[0]
    return f"chroma_db_{base_name}"

def load_extraction_to_langchain(json_path, collection_name=None):
    """
    Load extraction JSON and store it in a LangChain-compatible vectorstore.
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")

    with open(json_path, 'r') as f:
        data = json.load(f)

    documents, table_rows = [], []

    for chunk in data.get("chunks", []):
        if not chunk.get("text"):
            continue
        doc, row = build_document_from_chunk(chunk)
        documents.append(doc)
        table_rows.append(row)

    df = pd.DataFrame(table_rows)
    table_path = json_path.replace(".json", "_table.csv")
    df.to_csv(table_path, index=False)
    print(f"Chunk table saved to: {table_path}")
    print(df.head())

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=openai_api_key
    )

    persist_directory = generate_persist_path(json_path, collection_name)

    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    vectorstore.persist()

    print(f"Added {len(documents)} chunks to LangChain-compatible vectorstore")
    print(f"Vector database stored at: {persist_directory}")

    return vectorstore

if __name__ == "__main__":
    json_path = "/Users/siddharthdileep/extracter/01471587/special/AA_MzAyNjI4OTkxNGFkaXF6a2N4.extraction.json"

    vectorstore = load_extraction_to_langchain(json_path)
    qa_chain = setup_chat_qa(vectorstore)

    print("\nChat QA System Initialized. Type 'exit' to quit.")
    while True:
        query = input("\nQuestion: ")
        if query.lower() in ['exit', 'quit']:
            break

        result = qa_chain({"question": query})

        print("\nAnswer:")
        print(result["answer"])

        print("\nSources:")
        for i, doc in enumerate(result["source_documents"][:2]):
            print(f"\n[{i+1}] Page: {doc.metadata.get('page', 'N/A')}, Type: {doc.metadata.get('chunk_type', 'N/A')}")
            print(f"Position for the source {doc.metadata.get("position")}")
            print(f"Excerpt: {doc.page_content[:100]}...")
