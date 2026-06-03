import logging
import os
from pathlib import Path

import fitz
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from groq import Groq


BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"
PDF_PATH = BASE_DIR / "data" / "report.pdf"
OUTPUT_DIR = BASE_DIR / "output"

load_dotenv(ENV_PATH)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_groq_api_key() -> str:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is missing. Please add it to the .env file.")
    return groq_api_key


def extract_pdf_text(pdf_path: Path, max_pages: int = 3) -> list[str]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    page_texts = []

    pages_to_read = min(max_pages, len(doc))
    for page_num in range(pages_to_read):
        page = doc[page_num]
        text = page.get_text()
        page_texts.append(text)

    doc.close()
    return page_texts


def structure_page_data(page_texts: list[str]) -> pd.DataFrame:
    data = []

    for index, text in enumerate(page_texts, start=1):
        data.append(
            {
                "page_no": index,
                "word_count": len(text.split()),
                "first_50_chars": text[:50],
            }
        )

    return pd.DataFrame(data)


def save_outputs(df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_DIR / "pages.csv", index=False)
    df.to_json(OUTPUT_DIR / "pages.json", orient="records")


def summarise_with_groq(page_texts: list[str]) -> str:
    all_text = "\n".join(page_texts)
    text_sample = all_text[:2000]

    client = Groq(api_key=get_groq_api_key())
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": "Summarise this in exactly 3 bullet points.\n\n" + text_sample,
            }
        ],
    )

    return response.choices[0].message.content


def visualise_word_count(df: pd.DataFrame) -> None:
    plt.bar(df["page_no"], df["word_count"])
    plt.title("Word Count Per Page")
    plt.xlabel("Page Number")
    plt.ylabel("Word Count")
    plt.show()


def main() -> None:
    logging.info("PDF processing pipeline started")

    page_texts = extract_pdf_text(PDF_PATH)
    logging.info("Text extracted from the PDF")

    df = structure_page_data(page_texts)
    logging.info("Extracted text structured into a pandas DataFrame")

    save_outputs(df)
    logging.info("Data saved as CSV and JSON files")

    summary = summarise_with_groq(page_texts)
    print(summary)
    logging.info("Summary created successfully")

    visualise_word_count(df)
    logging.info("Visualisation created successfully")


if __name__ == "__main__":
    main()
