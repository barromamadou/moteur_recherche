import os
import fitz  # PyMuPDF
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in
from whoosh.analysis import StemmingAnalyzer

schema = Schema(
    title=ID(stored=True),
    content=TEXT(analyzer=StemmingAnalyzer(), stored=True)
)

if not os.path.exists("indexdir"):
    os.mkdir("indexdir")
ix = create_in("indexdir", schema)

writer = ix.writer()
pdf_dir = "corpus"

for filename in os.listdir(pdf_dir):
    if filename.endswith(".pdf"):
        path = os.path.join(pdf_dir, filename)
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        writer.add_document(title=filename, content=text)
        print(f"{filename} indexé.")
writer.commit()
print("Indexation terminée.")
