from pathlib import Path
import sys

import pypdf


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: extract_pdf_text.py <pdf>")
    path = Path(sys.argv[1])
    reader = pypdf.PdfReader(str(path))
    print(f"pages {len(reader.pages)}")
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        print(f"--- PAGE {index} ---")
        print(text[:5000])


if __name__ == "__main__":
    main()
