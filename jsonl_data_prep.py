from openai import OpenAI
import os
import re
import fitz
from config import Config
import json

# Initialize OpenAI client
CFG = Config()
client = OpenAI()
client.api_key = CFG.openai_api_key

source_data_folder = 'sources_data_3'

def anonymize_content(text):
    """
    Anonymizes email addresses and potentially sensitive or identifiable information.
    """
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '<email address>', text)
    return text

def read_text_from_pdf(file_path):
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    """
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def split_text(text, max_length=4000):
    """
    Splits the text into chunks of max_length characters.
    """
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]


def process_file_content(file_content):
    segments = split_text(file_content)
    all_qa_pairs = []

    for segment in segments:
        prompt = (
                "Generate detailed questions and answers that delve into the complexities of investment strategies, including topics like trading, risk management, "
                "and financial instruments such as gold, commodities, and forex. Explore the nuances of investment fundamentals, technical analytics, "
                "and the effective use of diverse investment tools. Reflect on the collective knowledge contained in an extensive collection of over 100 specialized sources "
                "in these fields. The responses should be insightful, providing clarity on sophisticated investment concepts and market analysis techniques. "
                "Format the output as a series of question and answer pairs, each clear, concise, and well-informed.\n\n"
                "Overview of topics based on a comprehensive library of investment-related literature:\n\n" + segment + "\n\n"
                                                                                                                        "Generate detailed questions and answers that resonate with the depth of information found in a vast array of investment literature."
        )

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": prompt
                }]
            )

            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content.strip()
                qa_pairs = content.split('\n\n')
                for pair in qa_pairs:
                    lines = pair.split('\n')
                    if len(lines) >= 2:
                        # Cleaning up the format and removing references to "document" or "text".
                        question = re.sub(r'^\d+\.\s*\**', '', lines[0].strip()).replace("Statement: ", "").replace(
                            "Instructions: ", "")
                        question = re.sub(r'(in|of) the document', '', question, flags=re.IGNORECASE).strip()
                        question = re.sub(r'(according to|based on) the text', '', question,
                                          flags=re.IGNORECASE).strip()
                        question = question.replace("**", "").replace("Q: ", "").strip("?:. ")
                        if question:  # Check if question is not empty
                            question = question[0].upper() + question[1:] + "?"

                        answer = lines[1].strip().replace("Response: ", "").replace("A: ", "").strip()
                        if answer:  # Check if answer is not empty
                            answer = answer[0].upper() + answer[1:]
                            answer = re.sub(r'the document (segment )?suggests?', '', answer,
                                            flags=re.IGNORECASE).strip()
                            answer = answer.replace("**", "")

                        all_qa_pairs.append({"input": question, "output": answer})
            else:
                print("No response or empty choices received from the API for a segment.")
        except Exception as e:
            print(f"Error calling API for a document segment: {e}")

    return all_qa_pairs


def main():
    output_jsonl_file = 'output_dataset.jsonl'
    file_names = os.listdir(source_data_folder)

    with open(output_jsonl_file, 'w', encoding='utf-8') as jsonlfile:
        for file_name in file_names:
            if file_name.startswith('.'):
                continue

            file_path = os.path.join(source_data_folder, file_name)
            print(f"Processing file: {file_name}")

            try:
                if file_name.lower().endswith('.txt'):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                        file_content = file.read()
                elif file_name.lower().endswith('.pdf'):
                    file_content = read_text_from_pdf(file_path)
                else:
                    print(f"Unsupported file type: {file_name}")
                    continue

                formatted_responses = process_file_content(file_content)
                for response in formatted_responses:
                    jsonlfile.write(json.dumps(response, ensure_ascii=False) + '\n')

            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

if __name__ == "__main__":
    main()