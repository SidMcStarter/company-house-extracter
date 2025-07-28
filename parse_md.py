def parse_markdown(file_path):
    """
    Parses a markdown file and returns its content as a string.
    
    :param file_path: Path to the markdown file.
    :return: Content of the markdown file as a string.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        print(f"Error: The file {file_path} does not exist.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None
    
    content = content.strip()
    chunk_list = []
    while content:
        chunk = {}
        ending_index = content.find("<!--")
        if ending_index == -1:
            chunk += content
            content = ""
        else:
            chunk += content[:ending_index].strip()
            content = content[ending_index + 4:].strip()
        break
    return chunk
        

if __name__ == "__main__":
    print(parse_markdown("/Users/siddharthdileep/extracter/01471587/special/AA_MzAyNjI4OTkxNGFkaXF6a2N4.extraction.md"))
    