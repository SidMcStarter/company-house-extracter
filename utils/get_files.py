import os, random
from utils.get_codes import get_codes

if __name__ == "__main__":
    directory = "01471587/filings"
    final_codes = {}

    for file in os.listdir(directory):
        code = file.split("_")[0]
        final_codes.setdefault(code, []).append(file)

    # Select one random file per code
    for code in final_codes:
        final_codes[code] = random.choice(final_codes[code])

    print(f"Found {len(final_codes)} codes in {directory}:")
    print(f"Total files found: {len(os.listdir(directory))}")
    
    shortened_directory = "01471587/shortened-filings"
    
    for (code, file) in final_codes.items():
        with open(f"{directory}/{file}", "rb") as f1:
            with open(f"{shortened_directory}/{file}", "wb") as f2:
                f2.write(f1.read())
                
