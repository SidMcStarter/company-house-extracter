import json
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain_community.llms import HuggingFaceHub
import os
from langchain_openai import OpenAI
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.vectorstores.utils import filter_complex_metadata
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings  # Add this instead

load_dotenv()

def setup_chat_qa(vectorstore, openai_api_key=None):
    """
    Set up a conversational QA system using the vectorstore and ChatGPT
    """
    openai_api_key = os.getenv("OPENAI_API_KEY") if not openai_api_key else openai_api_key

    # Initialize ChatOpenAI language model
    chat_model = ChatOpenAI(
        temperature=0.1,
        openai_api_key=openai_api_key,
        model="gpt-4o",  # You can also use "gpt-3.5-turbo" for lower cost
    )
    
    # Set up conversation memory - FIX: Add output_key parameter
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"  # Tell memory which output to store
    )
    
    # Create a conversational retrieval chain
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=chat_model,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        memory=memory,
        return_source_documents=True
    )
    
    return qa_chain

def load_extraction_to_langchain(json_path, collection_name=None):
    """
    Load extraction JSON into LangChain compatible vectorstore
    """
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # Load the extraction JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Prepare documents for LangChain
    documents = []
    table_rows = []
    
    # Extract chunks and maintain context
    for chunk in data["chunks"]:
        # Skip empty chunks
        if not chunk.get("text"):
            continue
        
        # Extract metadata for context
        metadata = {
            "chunk_id": chunk.get("chunk_id", ""),
            "chunk_type": chunk.get("chunk_type", "")
        }
        
        # Add grounding information if available
        if "grounding" in chunk and chunk["grounding"]:
            for g in chunk["grounding"]:
                if "box" in g:
                    metadata.update({
                        "page": g.get("page", 0),
                        "position": f"l={g['box'].get('l', 0):.2f}, t={g['box'].get('t', 0):.2f}, r={g['box'].get('r', 0):.2f}, b={g['box'].get('b', 0):.2f}"
                    })
                    break
        
        # Create LangChain Document
        doc = Document(
            page_content=chunk.get("text", ""),
            metadata=metadata
        )
        documents.append(doc)
                # Store for table
        row = metadata.copy()
        row["page_content"] = chunk.get("text", "")
        table_rows.append(row)
    
    # Initialize HuggingFace embeddings
    # embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",  # More efficient model
    openai_api_key=openai_api_key
    )
    
    df = pd.DataFrame(table_rows)
    table_path = json_path.replace(".json", "_table.csv")
    df.to_csv(table_path, index=False)
    print(f"Chunk table saved to: {table_path}")
    print(df.head())
    
    # Generate a collection name if not provided
    if collection_name is None:
        base_name = os.path.basename(json_path).split('.')[0]
        persist_directory = f"chroma_db_{base_name}"
    else:
        persist_directory = f"chroma_db_{collection_name}"
    
    # Create vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory
    )
    
    # Persist the vectorstore
    vectorstore.persist()
    
    print(f"Added {len(documents)} chunks to LangChain-compatible vectorstore")
    print(f"Vector database stored at: {persist_directory}")
    
    return vectorstore

if __name__ == "__main__":
    json_path = "/Users/siddharthdileep/extracter/01471587/special/AA_MzAyNjI4OTkxNGFkaXF6a2N4.extraction.json"
    
    # Load into LangChain vectorstore
    vectorstore = load_extraction_to_langchain(json_path)
    
    # Set up Chat QA system
    qa_chain = setup_chat_qa(vectorstore)
    
    # Interactive QA loop
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
            print(f"Excerpt: {doc.page_content[:100]}...")