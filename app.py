from glob import glob
import os

from flask import Flask, abort, request, render_template

import markdown

app = Flask(__name__)

WRITINGS_DIR = os.path.join(os.path.dirname(__file__), 'writings')

def format_title(title):
    return title.replace("_", " ").capitalize()

def get_piece(title, rev="current"):
    piece_dir = os.path.join(WRITINGS_DIR, title)
    if os.path.isdir(piece_dir):
        with open(os.path.join(piece_dir, '{}.md'.format(rev))) as content:
            return render_template(
                'piece.html',
                title=format_title(title),
                slug=title,
                content=markdown.markdown(content.read()),
                rev=rev,
                revs=["2", "1"]
            )
    abort(404)

@app.route("/")
def home():
    pieces = os.listdir(WRITINGS_DIR)
    pieces = {p: format_title(p) for p in pieces}
    return render_template('index.html', pieces=pieces)

@app.route("/<string:title>")
def piece(title):
    return get_piece(title)

@app.route("/<string:title>/rev/<int:rev>")
def revision(title, rev):
    return get_piece(title, "rev{}".format(rev))

@app.route("/new_piece", methods=['POST'])
def new_piece():
    if len(request.files) > 1:
        abort(400, 'Only one file at a time, please')

    piece_title = list(request.files.keys())[0]
    piece_dir = os.path.join(WRITINGS_DIR, piece_title)

    if os.path.isdir(piece_dir):
        current_revisions = len(glob(os.path.join(piece_dir, "rev*.md")))
        os.rename(
            os.path.join(piece_dir, "current.md"),
            os.path.join(piece_dir, 'rev{}.md'.format(current_revisions + 1))
        )
    else:
        os.mkdir(piece_dir)

    request.files[piece_title].save(os.path.join(piece_dir, "current.md"))

    return '', 201
