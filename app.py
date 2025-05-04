from flask import Flask, render_template, request
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from collections import Counter
import os

port = int(os.environ.get("PORT", 5000))

app = Flask(__name__)
ix = open_dir("indexdir")
search_stats = []

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
                    "content": hit.highlights("content") or hit["content"][:300] + "..."
                })
    return render_template("index.html", results=results, query=query)

@app.route("/stats")
def stats():
    counter = Counter(search_stats)
    return render_template("stats.html", stats=counter.most_common())

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port)