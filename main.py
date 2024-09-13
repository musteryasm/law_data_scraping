import os
import requests
import pandas as pd
from pdf2image import convert_from_path
import pytesseract

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image)
    return text

def summarize_text_openai(api_key, text):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Summarize the following text and extract the following information: 1) Verdict of the case, 2) Type of settlement, 3) Respondent. Clean and format the response to highlight these details. {text}"}
        ],
        "max_tokens": 500,
        "temperature": 0.5
    }
    try:
        response = requests.post(url, headers=headers, json=data, verify=False)
        response.raise_for_status()
        response_json = response.json()
        summary = response_json.get('choices', [{}])[0].get('message', {}).get('content', '')
        return summary
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return ""

def parse_summary(summary):
    lines = summary.split('\n')
    verdict = ""
    settlement = ""
    respondent = ""
    
    for line in lines:
        if "verdict" in line.lower():
            verdict = line.strip()
        elif "settlement" in line.lower():
            settlement = line.strip()
        elif "respondent" in line.lower():
            respondent = line.strip()
    
    return {
        "Verdict": verdict,
        "Settlement": settlement,
        "Respondent": respondent
    }

def get_pdf_files_from_folder(folder_path):
    """Return a list of all PDF file paths in the specified folder."""
    return [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.pdf')]

def main(api_key, folder_path, output_csv):
    pdf_files = get_pdf_files_from_folder(folder_path)
    records = []
    
    for pdf_path in pdf_files:
        print(f"Processing {pdf_path}...")
        text = extract_text_from_pdf(pdf_path)
        summary = summarize_text_openai(api_key, text)
        print(f"Summary for {pdf_path}: {summary}")
        details = parse_summary(summary)
        records.append(details)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(records)
    df.to_csv(output_csv, index=False)
    print(f"Data saved to {output_csv}")

if __name__ == "__main__":
    api_key = ""  
    folder_path = "./" 
    output_csv = "summarized_data.csv"
    main(api_key, folder_path, output_csv)
