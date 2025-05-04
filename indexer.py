from langdetect import detect
from PyPDF2 import PdfReader
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in
import os, shutil

corpus_dir = "corpus"
index_dir = "indexdir"

# Supprime l'ancien index
if os.path.exists(index_dir):
    shutil.rmtree(index_dir)

# Ajout du champ 'filename' dans le schéma
schema = Schema(
    title=ID(stored=True),
    content=TEXT(stored=True),
    filename=ID(stored=True)  # nouveau champ
)

os.mkdir(index_dir)
ix = create_in(index_dir, schema)
writer = ix.writer()

for filename in os.listdir(corpus_dir):
    if filename.endswith(".pdf"):
        path = os.path.join(corpus_dir, filename)
        try:
            text = ""
            reader = PdfReader(path)
            for page in reader.pages:
                text += page.extract_text() or ""
            if detect(text[:1000]) == "fr":
                writer.add_document(
                    title=filename,
                    content=text,
                    filename=filename  # Enregistrement du nom du fichier
                )
                print(f"Indexé : {filename}")
            else:
                print(f"Ignoré (non-français) : {filename}")
        except Exception as e:
            print(f"Erreur avec {filename} : {e}")

writer.commit()
print("✅ Indexation terminée.")
