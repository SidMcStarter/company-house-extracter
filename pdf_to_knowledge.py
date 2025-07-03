# pdf_qa_with_ollama.py

from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import requests, time
from dotenv import load_dotenv
import os

# Azure OCR Setup
load_dotenv()
AZURE_KEY = os.getenv("AZURE_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

client = ComputerVisionClient(
    AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY)
)

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, "rb") as f:
        result = client.read_in_stream(f, raw=True)

    operation_id = result.headers["Operation-Location"].split("/")[-1]

    # Poll for result
    while True:
        read_result = client.get_read_result(operation_id)
        if read_result.status not in ['notStarted', 'running']:
            break
        time.sleep(1)

    text_output = ""
    if read_result.status == OperationStatusCodes.succeeded:
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                text_output += line.text + "\n"
    return text_output

# PDF File Path
pdf_path = "./documents/file2.pdf"  # Replace with actual path
pdf_text = extract_text_from_pdf(pdf_path)

with open("./documents/extracted_text.txt", "w", encoding="utf-8") as out_file:
    out_file.write(pdf_text)

# Ask user question
user_question = input("Enter your question: ")

# Ask the Ollama model (running locally)
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:1b",  # Replace with the model you've pulled like llama3
        "prompt": f"The following is the content of a PDF:\n\n{pdf_text}\n\nQuestion: {user_question}\nAnswer:",
        "stream": False
    }
)

if response.status_code == 200:
    answer = response.json().get("response", "No 'response' field in output.")
    print("\nAnswer:\n" + answer)
else:
    print(f"\n[ERROR] Ollama server responded with status {response.status_code}")
    print("Raw response:", response.text)
