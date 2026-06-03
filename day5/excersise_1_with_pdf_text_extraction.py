import fitz  # PyMuPDF


def read_pdf(pdf_path: str) -> None:
    doc = fitz.open(pdf_path)

    print(f"Pages: {len(doc)}")
    print(f"Title: {doc.metadata.get('title', 'N/A')}")
    print(f"Author: {doc.metadata.get('author', 'N/A')}")

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()

        print(f"\n--- Page {page_num} ---")
        print(text.strip())

    doc.close()


if __name__ == "__main__":
    read_pdf("input.pdf")
