from os import listdir
from os.path import isfile, join

def get_codes(directory):
    """
    Get all codes from the specified directory.
    
    Args:
        directory (str): The path to the directory containing code files.
        
    Returns:
        list: A list of code file names in the directory.
    """
    files = [f for f in listdir(directory) if isfile(join(directory, f))]
    print(f"Total files in {directory}: {len(files)}")
    codes = {}
    for file in files:
        code = file.split('_')[0]
        if code not in codes:
            codes[code] = 1
        else:
            codes[code] += 1
        
    print(f"Found {len(codes)} codes in {directory}: {codes}")
    return codes

if __name__ == "__main__":
    directory = "01471587/filings"  # Change this to your directory path
    codes = get_codes(directory)
    # Here you can call put_codes(codes) if needed

