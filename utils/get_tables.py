import json
import pandas as pd
import re
import io
import os


def get_tables(json_file_path):
    """
    Extract tables from extraction JSON file and convert them to pandas DataFrames.
    
    Args:
        json_file_path (str): Path to the extraction JSON file
        
    Returns:
        dict: A dictionary mapping table chunk_ids to pandas DataFrames
    """
    # Load JSON file
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    
    tables = {}
    table_count = 0
    
    # Find all chunks with type "table"
    for chunk in data.get("chunks", []):
        if chunk.get("chunk_type") == "table" and "text" in chunk:
            table_id = chunk.get("chunk_id", f"table_{table_count}")
            table_count += 1
            table_text = chunk["text"]
            
            try:
                # Try pandas read_html first
                if "<table>" in table_text:
                    try:
                        dfs = pd.read_html(io.StringIO(table_text))
                        if dfs:
                            tables[table_id] = dfs[0]
                            continue
                    except Exception:
                        pass  # Fall back to other methods
                
                # Try parsing markdown-style tables with | separators
                lines = table_text.strip().split('\n')
                markdown_rows = []
                
                for line in lines:
                    line = line.strip()
                    if '|' in line:
                        # Strip leading/trailing |
                        if line.startswith('|'):
                            line = line[1:]
                        if line.endswith('|'):
                            line = line[:-1]
                        
                        # Split by | and clean cells
                        cells = [cell.strip() for cell in line.split('|')]
                        markdown_rows.append(cells)
                
                if markdown_rows:
                    # Check for separator row (like: ---|---|---)
                    has_separator = False
                    if len(markdown_rows) > 1:
                        potential_separator = markdown_rows[1]
                        has_separator = all(not cell or re.match(r'^[-:]+$', cell) for cell in potential_separator)
                    
                    if has_separator:
                        headers = markdown_rows[0]
                        data_rows = markdown_rows[2:]  # Skip the separator row
                    else:
                        headers = markdown_rows[0]
                        data_rows = markdown_rows[1:]
                    
                    # Normalize row lengths
                    if headers and data_rows:
                        max_cols = max(len(row) for row in [headers] + data_rows)
                        headers = headers + [''] * (max_cols - len(headers))
                        data_rows = [row + [''] * (max_cols - len(row)) for row in data_rows]
                        
                        df = pd.DataFrame(data_rows, columns=headers)
                        tables[table_id] = df
                        continue
                
                # Try space-aligned tables as last resort
                space_rows = []
                for line in lines:
                    if line.strip():
                        # Split by multiple spaces
                        cells = [cell for cell in re.split(r'\s{2,}', line.strip()) if cell]
                        if cells:
                            space_rows.append(cells)
                
                if space_rows:
                    # Normalize row lengths
                    max_cols = max(len(row) for row in space_rows)
                    space_rows = [row + [''] * (max_cols - len(row)) for row in space_rows]
                    
                    headers = space_rows[0]
                    data_rows = space_rows[1:]
                    
                    df = pd.DataFrame(data_rows, columns=headers)
                    tables[table_id] = df
            
            except Exception as e:
                print(f"Error parsing table {table_id}: {str(e)}")
    
    return tables

def export_all_tables_to_dataframe(tables_dict):
    """
    Combine all table DataFrames into one DataFrame with an added 'table_id' column.
    
    Args:
        tables_dict (dict): Mapping of table_id -> DataFrame
    
    Returns:
        pd.DataFrame: Combined DataFrame of all tables
    """
    combined_tables = []

    for table_id, df in tables_dict.items():
        df_copy = df.copy()
        df_copy["table_id"] = table_id  # add table_id column
        combined_tables.append(df_copy)
    
    combined_df = pd.concat(combined_tables, ignore_index=True)
    return combined_df

def display_tables(tables):
    """Display extracted tables with their IDs and some information"""
    if not tables:
        print("No tables found in the document.")
        return
        
    print(f"\nFound {len(tables)} tables:")
    
    for table_id, df in tables.items():
        print(f"\n{'=' * 60}")
        print(f"TABLE: {table_id}")
        print(f"{'=' * 60}")
        print(f"Shape: {df.shape} (rows × columns)")
        print(f"Columns: {', '.join(str(c) for c in df.columns)}")
        print("\nSample data:")
        print(df.head(3))
        

def process_query(query, json_file_path):
    """
    Process a user query to determine whether to extract tables or answer a question
    
    Args:
        query (str): User's query
        json_file_path (str): Path to the JSON file
        
    Returns:
        tuple: (tool_name, result)
    """
    # Check if this is a request for tables
    table_keywords = ["get tables", "extract tables", "show tables", 
                     "find tables", "list tables", "all tables"]
    
    if any(keyword in query.lower() for keyword in table_keywords):
        # Call the get_tables function
        tables = get_tables(json_file_path)
        return "get_tables", tables
    else:
        # This would be handled by a different function
        return "answer_question", f"Answering: {query}"

if __name__ == "__main__":
    # Default file path - adjust as needed
    json_file_path = "01471587/special/AA_MzAyNjI4OTkxNGFkaXF6a2N4.extraction.json"
    
    # Check if file exists
    if not os.path.isfile(json_file_path):
        print(f"Error: File not found at {json_file_path}")
        print("Please provide the correct path to an extraction JSON file.")
        exit(1)
    
    print(f"Testing table extraction from {json_file_path}")
    
    # Test direct function call
    print("\n===== Testing direct function call =====")
    tables = get_tables(json_file_path)
    display_tables(tables)
    