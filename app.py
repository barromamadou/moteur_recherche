from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from collections import Counter
from whoosh.index import open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
import fitz  # PyMuPDF
import os

# Configuration de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scientific.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialisation des extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Statistiques
search_stats = []

# Modèles
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

# Authentification
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dossier d’index Whoosh
ix = open_dir("indexdir")

# Routes

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    query = ""
    if request.method == "POST":
        query = request.form["query"]
        search_stats.append(query)
        with ix.searcher() as searcher:
            parser = QueryParser("content", ix.schema)
            myquery = parser.parse(query)
            found = searcher.search(myquery, limit=10)
            for hit in found:
                results.append({
                    "title": hit["title"],
                    "content": hit.highlights("content") or hit["content"][:300] + "...",
                    "filename": hit["filename"]
                })
    return render_template("index.html", results=results, query=query)

@app.route("/pdf/<path:filename>")
def pdf(filename):
    return send_from_directory("corpus", filename)

@app.route("/stats")
def stats():
    counter = Counter(search_stats)
    return render_template("stats.html", stats=counter.most_common())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
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
        email = request.form["email"]
        password = request.form["password"]
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
        title = request.form["title"]
        file = request.files.get("file", None)
        texte_libre = request.form.get("texte_libre", "").strip()

        if file and file.filename != "":
            # Sauvegarde fichier
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # Indexation fichier (comme vu précédemment)
            # ...

        elif texte_libre:
            # Sauvegarde texte libre dans fichier
            filename = f"resource_{current_user.id}_{len(texte_libre)}.txt"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(texte_libre)

            # Indexation texte (comme vu précédemment)
            # ...

        else:
            return "Erreur : veuillez fournir un fichier ou un texte."

        # Sauvegarde base de données, redirection, etc.

    return render_template("upload.html")


# Initialisation de la base de données (à lancer une seule fois ou via un script séparé)
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from collections import Counter
import os

# Configuration de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'barro'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scientific.db'
app.config['UPLOAD_FOLDER'] = 'uploads'

# Initialisation des extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Statistiques
search_stats = []

# Modèles
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

# Authentification
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Dossier d’index Whoosh
ix = open_dir("indexdir")

# Routes

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    query = ""
    if request.method == "POST":
        query = request.form["query"]
        search_stats.append(query)
        with ix.searcher() as searcher:
            parser = QueryParser("content", ix.schema)
            myquery = parser.parse(query)
            found = searcher.search(myquery, limit=10)
            for hit in found:
                results.append({
                    "title": hit["title"],
                    "content": hit.highlights("content") or hit["content"][:300] + "...",
                    "filename": hit["filename"]
                })
    return render_template("index.html", results=results, query=query)

@app.route("/pdf/<path:filename>")
def pdf(filename):
    return send_from_directory("corpus", filename)

@app.route("/stats")
def stats():
    counter = Counter(search_stats)
    return render_template("stats.html", stats=counter.most_common())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
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
        email = request.form["email"]
        password = request.form["password"]
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
        title = request.form["title"]
        file = request.files["file"]
        if file and file.filename.endswith(".pdf"):
            filename = file.filename
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            resource = Resource(title=title, filename=filename, user_id=current_user.id)
            db.session.add(resource)
            db.session.commit()
            return redirect(url_for("index"))
        else:
            return "Veuillez envoyer un fichier PDF valide."
    return render_template("upload.html")

# Initialisation de la base de données (à lancer une seule fois ou via un script séparé)
@app.before_first_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
