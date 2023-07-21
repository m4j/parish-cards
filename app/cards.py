from flask import Flask, render_template, abort, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from . import stjb
from . import member as m
from . import prosphora as p
from .application import ApplicationForm
from .database import db, Application
import os
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '606d2fc4-31cb-4ce1-a35b-346ec660994d'
bootstrap = Bootstrap(app)

db_uri = os.environ['STJB_DATABASE_URI']
# for legacy sqlite3 connection
db_path = urlparse(db_uri).path
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
db.init_app(app)

class SearchForm(FlaskForm):
    name = StringField('Type name, like “irina”, or “Иван”. Partial name works too, like “mar” or “joh”', validators=[DataRequired()], render_kw={'autofocus': True})
    submit = SubmitField('Search')

@app.route('/', methods=['GET', 'POST'])
def index():
    return directory(
            redirect_url=url_for('index'),
            entity=m.Member,
            template='index.html',
            member_url='.member')

@app.route('/books', methods=['GET', 'POST'])
def books():
    return directory(
            redirect_url=url_for('books'),
            entity=p.Member,
            template='books.html',
            member_url='.book')

@app.route("/applications")
def applications():
    apps = db.session.execute(db.select(Application).order_by(Application.signature_date)).scalars()
    return render_template("applications.html", apps=apps)

@app.route('/application/add', methods=['GET', 'POST'])
def application_add():
    form = ApplicationForm()
    members = []
    if form.validate_on_submit():
        result = application_form.process(form)
        guid = result[0]
        errors = result[1]
        if errors:
            flash(errors)
        if guid:
            return redirect(url_for('member', guid=guid))
    return render_template( 'application.html', form=form)

def directory(redirect_url, member_url, entity, template):
    form = SearchForm()
    members = []
    if form.validate_on_submit():
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(redirect_url)
    name = session.get('name')
    if name:
        session['name'] = None
        connection = stjb.connect(db_path)
        members = entity.find_all_by_name(connection, name)
        connection.close()
        if len(members) == 0:
            flash('Nothing found, please try again')
    return render_template(
            template,
            form=form,
            members=members,
            member_url=member_url)

@app.route('/member/<guid>')
def member(guid):
    connection = stjb.connect(db_path)
    entity = m.Member.find_by_guid(connection, guid)
    if not entity:
        connection.close()
        abort(404)
    entity.load_payments(connection)
    connection.close()
    return render_template('member.html', member=entity)

@app.route('/book/<guid>')
def book(guid):
    connection = stjb.connect(db_path)
    entity = p.Member.find_by_guid(connection, guid)
    if not entity:
        connection.close()
        abort(404)
    entity.load_payments(connection)
    connection.close()
    return render_template('member.html', member=entity)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
