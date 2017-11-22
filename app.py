from functools import wraps
from glob import glob
import os

from flask import Flask, flash, abort, redirect, request, render_template, send_file, session, url_for

import markdown

app = Flask(__name__)
app.config.from_pyfile('config.cfg')

WRITINGS_DIR = os.path.join(os.path.dirname(__file__), 'writings')

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('logged_in', False):
            return f(*args, **kwargs)
        return redirect(url_for('login'))
    return decorated

def format_title(title):
    return title.replace("_", " ").capitalize()

def current_revisions(title):
    piece_dir = os.path.join(WRITINGS_DIR, title)
    return len(glob(os.path.join(piece_dir, "rev*.md")))

def piece_html(title, rev="current"):
    piece_dir = os.path.join(WRITINGS_DIR, title)

    if os.path.isdir(piece_dir):
        rev_count = current_revisions(title)
        revs = [str(r) for r in reversed(range(1, rev_count + 1))]

        with open(os.path.join(piece_dir, '{}.md'.format(rev))) as content:
            return render_template(
                'piece.html',
                title=format_title(title),
                slug=title,
                content=markdown.markdown(content.read()),
                rev=rev,
                revs=revs
            )
    abort(404)

def piece_md(title, rev="current"):
    piece_dir = os.path.join(WRITINGS_DIR, title)

    if os.path.isdir(piece_dir):
        print(title, rev)
        return send_file(
            os.path.join(piece_dir, rev) + ".md",
            as_attachment=True,
            attachment_filename="{}_{}.md".format(title, rev)
        )
    abort(404)

@app.route("/")
@requires_auth
def home():
    pieces = os.listdir(WRITINGS_DIR)
    pieces = {p: format_title(p) for p in pieces}
    return render_template('index.html', pieces=pieces)

@app.route("/<string:title>")
@requires_auth
def piece(title):
    return_type = request.args.get('format', 'html')

    if return_type == 'md':
        return piece_md(title)

    return piece_html(title)

@app.route("/<string:title>/rev/<int:rev>")
@requires_auth
def revision(title, rev):
    return_type = request.args.get('format', 'html')

    if return_type == 'md':
        return piece_md(title, "rev{}".format(rev))

    return piece_html(title, "rev{}".format(rev))

@app.route("/new_piece", methods=['POST'])
def new_piece():
    if len(request.files) > 1:
        abort(400, 'Only one file at a time, please')

    piece_title = list(request.files.keys())[0]
    piece_dir = os.path.join(WRITINGS_DIR, piece_title)

    if os.path.isdir(piece_dir):
        rev_count = current_revisions(piece_title)
        os.rename(
            os.path.join(piece_dir, "current.md"),
            os.path.join(piece_dir, 'rev{}.md'.format(rev_count + 1))
        )
    else:
        os.mkdir(piece_dir)

    request.files[piece_title].save(os.path.join(piece_dir, "current.md"))

    return '', 201

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == app.config['PASSWORD']:
            session['logged_in'] = True
            return redirect(url_for('home'))
        flash('Wrong password')
    return render_template('login.html')
