import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config
from neo4j import GraphDatabase
import os
# --- Neo4j Connection ---
@st.cache_resource
def get_driver():
    # Replace with your Neo4j credentials
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = os.getenv("NEO4J_PASSWORD")  
    return GraphDatabase.driver(uri, auth=(user, password))

driver = get_driver()

def get_graph_data():
    with driver.session() as session:
        result = session.run("""
            MATCH (n)-[r]->(m)
            RETURN n, r, m
            LIMIT 25
        """)
        nodes = set()
        edges = []
        for record in result:
            n = record["n"]
            r = record["r"]
            m = record["m"]

            # Correctly handle frozenset for labels
            n_label = list(n.labels)[0] if n.labels else ""
            m_label = list(m.labels)[0] if m.labels else ""

            nodes.add(Node(id=n.element_id, label=n_label, **dict(n)))
            nodes.add(Node(id=m.element_id, label=m_label, **dict(m)))
            edges.append(Edge(source=r.start_node.element_id,
                              target=r.end_node.element_id,
                              type=type(r).__name__))
    return list(nodes), edges

# --- Streamlit App ---
st.title("Neo4j Graph Visualization with Streamlit")

nodes, edges = get_graph_data()

config = Config(width=750,
                height=950,
                directed=True,
                physics=True,
                hierarchical=False,
                )

return_value = agraph(nodes=nodes,
                      edges=edges,
                      config=config)

st.write("Selected Node:", return_value)