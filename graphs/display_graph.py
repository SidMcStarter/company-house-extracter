from pyvis.network import Network
import streamlit.components.v1 as components
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv



def generate_graph_html(NEO4J_URI=None, NEO4J_USER=None, NEO4J_PASSWORD=None, company_name = None, file_name=None):
    print("Generating graph HTML...", file_name)
    net = Network(height="600px", width="100%", notebook=False)
    net.force_atlas_2based()

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        if file_name:
            result = session.run(
                """
                MATCH (a)-[r]->(b)
                WHERE a.source_file = $file OR b.source_file = $file OR r.source_file = $file
                RETURN a, r, b LIMIT 100
                """,
                file=file_name + ".txt"
            )
        else:
            result = session.run("MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 100")
        for record in result:
            a = record["a"]
            b = record["b"]
            r = record["r"]

            a_label = f"{next(iter(a.labels))}: {a.get('id', a.id)}"
            b_label = f"{next(iter(b.labels))}: {b.get('id', b.id)}"
            a_title = f"Labels: {', '.join(a.labels)}<br>Properties: {dict(a)}"
            b_title = f"Labels: {', '.join(b.labels)}<br>Properties: {dict(b)}"
            net.add_node(a.id, label=a_label, title=a_title)
            net.add_node(b.id, label=b_label, title=b_title)
            net.add_edge(a.id, b.id, label=r.type)
            

    driver.close()

    # Add some styling options
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "size": 12,
          "face": "Tahoma"
        },
        "shape": "dot",
        "size": 20
      },
      "edges": {
        "font": {
          "size": 10,
          "align": "middle"
        },
        "color": "gray",
        "smooth": false,
        "width": 1,
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -80000,
          "springLength": 250,
          "springConstant": 0.001
        },
        "minVelocity": 0.75
      }
    }
    """)

    temp_path = f"{company_name}/graphs/{file_name}_graph.html"
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    net.save_graph(temp_path)
    return temp_path

if __name__ == "__main__":
    load_dotenv()
    # Define Neo4j credentials
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
    print(f"Using Neo4j URI: {NEO4J_URI}, User: {NEO4J_USERNAME}")

    # Call the function
    graph_html_path = generate_graph_html(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

    # Print the path to the generated HTML file
    print(f"Graph HTML saved at: {graph_html_path}")