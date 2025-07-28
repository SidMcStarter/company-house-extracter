from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from pydantic import Field
from langchain.chains.base import Chain
from typing import Dict, Any, List
import os
# Updated import for Neo4jGraph
from langchain_neo4j import Neo4jGraph
from langchain_community.graphs import Neo4jGraph as CommunityNeo4jGraph

def answer_question_with_text(messages, text_file_path, llm_model="gpt-4o-mini"):
    """
    Given a list of messages (chat history) and a text file path,
    returns the answer to the latest question using the file's content.
    """
    with open(text_file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Combine messages into a prompt (simple example)
    chat_history = "\n".join([f"User: {m['user']}\nAssistant: {m.get('assistant','')}" for m in messages[:-1]])
    latest_question = messages[-1]['user']
    prompt = f"{chat_history}\nUser: {latest_question}\n\nContext:\n{text}\n\nAnswer:"

    llm = ChatOpenAI(model=llm_model, temperature=0.0)
    response = llm.invoke(prompt)
    return response

def create_graph_chain(neo4j_uri, neo4j_username, neo4j_password, llm_model="gpt-4o-mini"):
    """Create and return a GraphCypherQAChain."""
    # Create the community-compatible graph object
    graph = CommunityNeo4jGraph(
        url=neo4j_uri,
        username=neo4j_username,
        password=neo4j_password
    )
    
    # Define the prompts with improved Cypher generation
    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question"],
        template="""
You are an expert in Cypher query language for Neo4j.
Given the following schema:

{schema}

Please write a valid Cypher query to answer this question:
{question}

The query should be as inclusive as possible, looking for any nodes or relationships that might contain relevant information.
Try different approaches if a direct match isn't likely:
- Look for text properties containing keywords
- Look for connected entities
- Check various relationship types

Return ONLY the Cypher query without any explanations or text before or after.
"""
    )
    
    qa_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template="""You are an assistant that helps to form nice and human understandable answers.
Based on the context and the question, provide a helpful response.
If the context doesn't contain relevant information, explain what was searched for and suggest refining the query.

Context: {context}
Question: {question}
"""
    )
    
    # Create the chain
    return GraphCypherQAChain.from_llm(
        ChatOpenAI(temperature=0, model_name=llm_model),
        graph=graph,
        cypher_prompt=cypher_prompt,
        qa_prompt=qa_prompt,
        verbose=True,
        allow_dangerous_requests=True
    )

class HybridRetrieval(Chain):
    """Chain that combines graph and vector search results."""
    
    graph_chain: Chain = Field(...)
    vector_index: Any = Field(...)
    
    @property
    def input_keys(self) -> List[str]:
        return ["query", "source_file"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["result"]
    
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        question = inputs["query"]
        #optionally get the source file
        source_file = inputs.get("source_file")
        
        # for source file provided, change the query by a little
        if source_file:
            graph_question = (
                f"Only consider nodes where source_file = '{source_file}'.\n\n"
                f"{question}"
            )
        else:
            graph_question = question
            
        try:
            # Get results from the Cypher QA chain
            graph_result = self.graph_chain.invoke(graph_question)
            graph_text = graph_result.get('result', "No graph results found")
        except Exception as e:
            graph_text = f"Graph query error: {str(e)[:100]}"
        
        # Get results from the vector retriever
        if source_file:
            vector_docs = self.vector_index.similarity_search(
                question, k=3, filter={"source_file": source_file}
            )
        else:
            vector_docs = self.vector_index.similarity_search(question, k=3)
        vector_result = "\n\n".join([doc.page_content for doc in vector_docs])
        
        # Combine the results into a single string
        combined_result = f"Graph Result:\n{graph_text}\n\nVector Results:\n{vector_result}"
        print(f"Combined Result:\n{combined_result}")
        return {"result": combined_result}

def create_hybrid_rag_chain(graph_chain, vector_index, llm_model="gpt-4o-mini"):
    """
    Creates a hybrid RAG chain that combines results from graph and vector search.
    
    Args:
        graph_chain: A GraphCypherQAChain instance
        vector_index: A vector store index
        llm_model: The model to use for the final response generation
        
    Returns:
        A chain that can be invoked with a query
    """
    # Initialize the hybrid retriever
    hybrid_retriever = HybridRetrieval(
        graph_chain=graph_chain,
        vector_index=vector_index
    )
    
    # Create the final QA chain
    template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
    prompt = ChatPromptTemplate.from_template(template)
    
    # Define the chain
    final_chain = {
        # pass the whole inputs dict ({'question':…, 'source_file':…})
        "context": lambda inputs: hybrid_retriever.invoke(inputs)["result"],
        "question": lambda inputs: inputs["query"],
    } | prompt | ChatOpenAI(temperature=0, model_name=llm_model) | StrOutputParser()
    
    return final_chain

def answer_with_hybrid_retrieval(
    query, 
    neo4j_uri, 
    neo4j_username, 
    neo4j_password, 
    vector_index, 
    llm_model="gpt-4o-mini",
    source_file=None
):
    """
    Process a query using hybrid retrieval (graph + vector) and return the response.
    
    Args:
        query: The user's question
        neo4j_uri: URI for Neo4j connection
        neo4j_username: Neo4j username
        neo4j_password: Neo4j password
        vector_index: Vector store index
        llm_model: Model to use for LLM operations
        
    Returns:
        The answer to the query
    """
    # Create the graph chain
    graph_chain = create_graph_chain(neo4j_uri, neo4j_username, neo4j_password, llm_model)
    
    # Create the RAG chain
    rag_chain = create_hybrid_rag_chain(graph_chain, vector_index, llm_model)
    
    # Run the chain and return the result
    return rag_chain.invoke({
        "query":       query,
        "source_file": source_file
    })

if __name__ == "__main__":
    # Test the hybrid retrieval function
    import os
    from dotenv import load_dotenv
    from langchain_neo4j import Neo4jVector
    from langchain_openai import OpenAIEmbeddings
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME") 
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    
    # Test queries with broader scope
    test_queries = [
        "What is this document about",
    ]
    
    # Connect to Neo4j for vector search
    print("Creating vector index...")
    vector_index = Neo4jVector.from_existing_graph(
        OpenAIEmbeddings(),
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        node_label="Document",
        text_node_properties=["text"],
        embedding_node_property="embedding",
    )
    print(vector_index.similarity_search("what is this document about", k=3, filter={"source_file": "TM01_MzA4ODM3NDQxOGFkaXF6a2N4.txt"}))
    """
    try:
        vector_index = Neo4jVector.from_existing_graph(
            OpenAIEmbeddings(),
            url=NEO4J_URI,
            username=NEO4J_USERNAME,
            password=NEO4J_PASSWORD,
            node_label="Document",
            text_node_properties=["text"],
            embedding_node_property="embedding",
        )
        
        
        # Test each query
        for query in test_queries:
            print(f"\n\n===== Testing: {query} =====")
            
            try:
                response = answer_with_hybrid_retrieval(
                    query=query,
                    neo4j_uri=NEO4J_URI,
                    neo4j_username=NEO4J_USERNAME,
                    neo4j_password=NEO4J_PASSWORD,
                    vector_index=vector_index,
                    llm_model="gpt-4o-mini",
                    source_file="TM01_MzA4ODM3NDQxOGFkaXF6a2N4.txt"  # Example file name, adjust as needed
                )
                
                print("\nResponse:")
                print(response)
            except Exception as e:
                print(f"Error processing query: {e}")
                import traceback
                traceback.print_exc()
        
        print("\nTesting complete!")
    except Exception as e:
        print(f"Error setting up vector index: {e}")
        import traceback
        traceback.print_exc()
    """