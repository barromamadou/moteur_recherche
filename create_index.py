import os
import fitz  # Pour lire les fichiers PDF
import docx  # Pour lire les fichiers DOCX
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in
from whoosh.analysis import StemmingAnalyzer

# Définir le schéma de l’index
schema = Schema(
    title=ID(stored=True),
    content=TEXT(analyzer=StemmingAnalyzer(), stored=True),
    filename=ID(stored=True)
)

# Dossier des fichiers à indexer
uploads_dir = "uploads"

# Créer le dossier d’index s’il n’existe pas
if not os.path.exists("indexdir"):
    os.mkdir("indexdir")

# Créer un index avec le schéma défini
ix = create_in("indexdir", schema)
writer = ix.writer()

# Fonction pour extraire texte d’un fichier DOCX
def extract_text_from_docx(path):
    try:
        doc = docx.Document(path)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Erreur lecture DOCX {path}: {e}")
        return ""

# Fonction pour extraire texte d’un fichier TXT
def extract_text_from_txt(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"Erreur lecture TXT {path}: {e}")
        return ""

# Parcourir tous les fichiers du dossier d’upload
for filename in os.listdir(uploads_dir):
    path = os.path.join(uploads_dir, filename)
    text = ""

    if filename.endswith(".pdf"):
        try:
            doc = fitz.open(path)
            for page in doc:
                text += page.get_text()
        except Exception as e:
            print(f"Erreur lecture PDF {filename} : {e}")
            continue

    elif filename.endswith(".docx"):
        text = extract_text_from_docx(path)

    elif filename.endswith(".txt"):
        text = extract_text_from_txt(path)

    else:
        print(f"Fichier ignoré (format non supporté) : {filename}")
        continue

    # Indexer le document dans Whoosh
    writer.add_document(
        title=filename,
        content=text,
        filename=filename
    )
    print(f"{filename} indexé.")

# Finaliser l’indexation
writer.commit()
print("Indexation terminée.")
