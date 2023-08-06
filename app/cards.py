from flask import Flask, render_template, abort, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from . import stjb
from . import member as m
from . import prosphora as p
from .application import ApplicationForm, ApplicantsRegistrationForm
from .database import db, Application, Person, Card, Marriage, find_member, find_person, find_marriage
import os
import uuid
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
    return render_template('applications.html', apps=apps)

@app.route('/application/add', methods=['GET', 'POST'])
def application_add():
    form = ApplicationForm()
    if form.validate_on_submit():
        app = Application(guid=uuid.uuid4())
        form.save_application(app)
        db.session.add(app)
        db.session.commit()
        return redirect(url_for('applications'))
    return render_template( 'application.html', form=form)

@app.route('/application/<guid>', methods=['GET', 'POST'])
def application_edit(guid):
    app = db.get_or_404(Application, uuid.UUID(guid))
    form = ApplicationForm()
    if form.validate_on_submit():
        form.save_application(app)
        db.session.commit()
        if form.save.data:
            flash('The application has been updated')
            return redirect(url_for('applications'))
        if form.register.data:
            flash('Please verify new member names and monthly dues, and then press Register')
            return redirect(url_for('application_register', guid=guid))
    form.load_application(app)
    return render_template( 'application.html', form=form)

def validate_and_consider_redirecting(guid, applicant):
    if applicant.do_register == 'as_member':
        member = find_member(applicant.en_name_first, applicant.en_name_last)
        if member:
            flash(f'{member.person.full_name_address()} is already a parish member')
            return redirect(url_for('application_register', guid=guid))
    person = find_person(applicant.en_name_first, applicant.en_name_last)
    if person:
        flash(f'Non member {person.full_name_address()} found')
        marriage = find_marriage(applicant.en_name_first, applicant.en_name_last)
        if marriage:
            flash(f'Marriage between {marriage.husband.full_name()} and {marriage.wife.full_name()} found')
        return redirect(url_for('application_register', guid=guid))
    return None

@app.route('/application/register/<guid>', methods=['GET', 'POST'])
def application_register(guid):
    app = db.get_or_404(Application, uuid.UUID(guid))
    form = ApplicantsRegistrationForm()
    if form.validate_on_submit():
        applicant = form.applicant()
        redirecting = validate_and_consider_redirecting(guid, applicant)
        if redirecting:
            return redirecting
        spouse = form.spouse()
        if spouse:
            redirecting = validate_and_consider_redirecting(guid, spouse)
            if redirecting:
                return redirecting
        person = Person(app, applicant)
        member = Card(app, person, applicant, form.as_of_date.data)
        db.session.add(person)
        db.session.add(member)
        if spouse:
            spouse_person = Person.create_spouse(app, spouse)
            db.session.add(spouse_person)
            husband = person if person.gender == 'M' else spouse_person
            wife = spouse_person if person.gender == 'M' else person
            marriage = Marriage(husband, wife)
            db.session.add(marriage)
            if spouse.do_register == 'as_member':
                spouse_member = Card(app, spouse_person, spouse, form.as_of_date.data)
                db.session.add(spouse_member)
        db.session.commit()
        flash('The application has been registered')
        return redirect(url_for('member', guid=member.guid))
    form.load_application(app)
    return render_template( 'register_members.html', form=form)

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
