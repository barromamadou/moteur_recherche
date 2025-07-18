import os
import fitz  # PyMuPDF pour PDF
import docx  # python-docx pour DOCX
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from whoosh.index import open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import QueryParser
from collections import Counter

# --- Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scientific.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Création dossier uploads s'il n'existe pas
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Modèles ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# --- Authentification ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Whoosh index ---
try:
    ix = open_dir("indexdir")
except:
    print("Erreur: dossier 'indexdir' non trouvé. Veuillez créer l'index avant de lancer l'app.")
    ix = None

# --- Statistiques simples ---
search_stats = []

# --- Fonctions utilitaires pour extraction texte ---
def extract_text_from_pdf(path):
    text = ""
    try:
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()
    except Exception as e:
        print(f"Erreur lecture PDF {path} : {e}")
    return text

def extract_text_from_docx(path):
    text = ""
    try:
        doc = docx.Document(path)
        text = "\n".join([p.text for p in doc.paragraphs])
    except Exception as e:
        print(f"Erreur lecture DOCX {path} : {e}")
    return text

def extract_text_from_txt(path):
    text = ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except Exception as e:
        print(f"Erreur lecture TXT {path} : {e}")
    return text

def index_document(title, filename):
    if ix is None:
        print("Index Whoosh non disponible.")
        return
    text = ""
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(path)
    elif filename.endswith(".docx"):
        text = extract_text_from_docx(path)
    elif filename.endswith(".txt"):
        text = extract_text_from_txt(path)
    else:
        print(f"Format non supporté pour indexation: {filename}")
        return
    writer = ix.writer()
    writer.add_document(title=title, content=text, filename=filename)
    writer.commit()
    print(f"Indexation terminée pour {filename}")

def get_document_type(filename):
    filename_lower = filename.lower()
    if 'article' in filename_lower or 'paper' in filename_lower:
        return 'articles'
    elif 'these' in filename_lower or 'thesis' in filename_lower:
        return 'theses'
    elif 'rapport' in filename_lower or 'report' in filename_lower:
        return 'reports'
    elif 'memoire' in filename_lower or 'memoir' in filename_lower:
        return 'memoires'
    elif filename.endswith('.pdf'):
        return 'articles'
    elif filename.endswith('.docx'):
        return 'reports'
    elif filename.endswith('.txt'):
        return 'memoires'
    return 'unknown'

# --- Routes principales ---
@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    query = ""
    filter_type = "all"
    
    if request.method == "POST":
        query = request.form.get("query", "")
        filter_type = request.form.get("filter", "all")
        search_stats.append(query)
        
        if ix:
            with ix.searcher() as searcher:
                parser = QueryParser("content", ix.schema)
                myquery = parser.parse(query)
                found = searcher.search(myquery, limit=100)  # Augmenter la limite
                
                for hit in found:
                    # Déterminer le type de document
                    doc_type = get_document_type(hit["filename"])
                    
                    # Filtrer selon le type sélectionné
                    if filter_type == "all" or filter_type == doc_type:
                        results.append({
                            "title": hit["title"],
                            "content": hit.highlights("content") or hit["content"][:300] + "...",
                            "filename": hit["filename"],
                            "type": doc_type
                        })
    
    return render_template("index.html", results=results, query=query, filter_type=filter_type)

@app.route("/pdf/<path:filename>")
def pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/stats")
def stats():
    counter = Counter(search_stats)
    return render_template("stats.html", stats=counter.most_common())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if User.query.filter_by(email=email).first():
            return "Email déjà utilisé"
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("index"))
        return "Identifiants invalides"
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        title = request.form.get("title")
        file = request.files.get("file", None)
        texte_libre = request.form.get("texte_libre", "").strip()

        if file and file.filename != "":
            if not any(file.filename.endswith(ext) for ext in [".pdf", ".docx", ".txt"]):
                return "Format de fichier non supporté. Seuls PDF, DOCX, TXT autorisés."
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            resource = Resource(title=title, filename=filename, user_id=current_user.id)
            db.session.add(resource)
            db.session.commit()

            index_document(title, filename)
            return redirect(url_for("index"))

        elif texte_libre:
            filename = f"resource_{current_user.id}_{len(texte_libre)}.txt"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(texte_libre)

            resource = Resource(title=title, filename=filename, user_id=current_user.id)
            db.session.add(resource)
            db.session.commit()

            index_document(title, filename)
            return redirect(url_for("index"))

        else:
            return "Erreur : veuillez fournir un fichier ou un texte."

    return render_template("upload.html")

with app.app_context():
    db.create_all()
    
if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
