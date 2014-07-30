# all the imports
import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from werkzeug.utils import secure_filename
import re

from jinja2 import evalcontextfilter, Markup, escape

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

# pagination idea: http://flask.pocoo.org/snippets/44/

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

UPLOAD_FOLDER = './static/images'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'recipes.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER=UPLOAD_FOLDER
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
    

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

        
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select id, title, ingredients, steps, tags, url from entries order by id asc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['GET', 'POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'POST':
        db = get_db()
        cur = db.execute('insert into entries (title, ingredients, steps, tags, url) values (?, ?, ?, ?, ?)', \
                     [request.form['title'], request.form['ingredients'], request.form['steps'], request.form['tags'], request.form['url']])
        db.commit()
        flash('New entry was successfully posted','success')
        return view_entry(str(cur.lastrowid))
    else:
        return render_template('add_entry.html')


@app.route('/delete/<id>')
def delete_entry(id):
    if not session.get('logged_in'):
        abort(401)

    db = get_db()
    db.execute('delete from entries where id = ?', [id.strip()])
    db.commit()
    flash('Entry ' + id + ' has been deleted','success')
    return redirect(url_for('show_entries'))


@app.route('/edit/<id>', methods=['GET', 'POST'])
def edit_entry(id):
    if not session.get('logged_in'):
        abort(401)

    if request.method == 'POST':
        db = get_db()
        db.execute('update entries set title = ?, ingredients = ?, steps = ?, tags = ?, url = ? where id = ?', \
                    [request.form['title'], request.form['ingredients'], request.form['steps'], request.form['tags'], request.form['url'], request.form['id']])
        db.commit()
        flash('Entry ' + id + ' has been modified.','success')
        return view_entry(str(id))
    else:
        db = get_db()
        cur = db.execute('select id, title, ingredients, steps, tags, url from entries where id = ? order by id desc', [id.strip()])
        entries = cur.fetchall()
        return render_template('edit_entry.html', entries=entries)


@app.route('/view/<id>')
def view_entry(id):
    db = get_db()
    cur = db.execute('select id, title, ingredients, steps, tags, url from entries where id = ? order by id desc', [id.strip()])
    entries = cur.fetchall()
    return render_template('view_entry.html', entries=entries)

@app.route('/search/<tag>', methods=['GET'])
@app.route('/search', methods=['GET', 'POST'])
def search(tag=None):
    db = get_db()
    if request.method == 'GET' and not tag:
        cur = db.execute('select tags from entries')
        entries = cur.fetchall()
        t = []
        tags = []
        for e in entries:
            t.extend(e[0].split(' '))
        t = list(set(t))
        for i in t:
            tags.append((i,))
        tags.sort()
        return render_template('search.html', entries=tags)
    
    if not tag:
        search = request.form['search_query']
    else:
        search = tag
        
    query = 'select id, title, ingredients, steps, tags, url from entries where'
    for t in search.split(' '):
        query += """ (tags like ('%' || ? || '%') or title like ('%' || ? || '%') or ingredients like ('%' || ? || '%')) AND """
    requests = search.split(' ')*3
    requests.sort()
    query = query[:-4] + 'order by id asc'
    if search:
        cur = db.execute(query, requests)
    else:
        cur = db.execute('select id, title, ingredients, steps, tags, url from entries order by id asc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and not session.get('logged_in'):
        db = get_db()
        cur = db.execute('select id, username, password from users where username = ? and password = ?', [request.form['username'], request.form['password']])
        rows = cur.fetchall()
        if len(rows) == 1:
            session['logged_in'] = True
        else:
            flash('Invalid username or password','error')
    return redirect(url_for('show_entries'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out','success')
    return redirect(url_for('show_entries'))


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
