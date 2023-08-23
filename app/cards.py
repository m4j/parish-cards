from flask import Flask, render_template, abort, session, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap
from . import stjb
from . import member as m
from . import prosphora as p
from .application import ApplicationForm, ApplicantsRegistrationForm, UpdateDecisionsForm
from .database import db, Application, Person, Card, Marriage, find_member, find_person, find_active_marriage, find_active_marriage_of_husband, find_active_marriage_of_wife
import os
import uuid
from urllib.parse import urlparse

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

stjb_app = Flask(__name__)
stjb_app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or '606d2fc4-31cb-4ce1-a35b-346ec660994d'
bootstrap = Bootstrap(stjb_app)

db_uri = os.environ['STJB_DATABASE_URI']
# for legacy sqlite3 connection
db_path = urlparse(db_uri).path
stjb_app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
db.init_app(stjb_app)

class SearchForm(FlaskForm):
    name = StringField('Type name, like “irina”, or “Иван”. Partial name works too, like “mar” or “joh”', validators=[DataRequired()], render_kw={'autofocus': True})
    submit = SubmitField('Search')

@stjb_app.route('/', methods=['GET', 'POST'])
def index():
    return directory(
            redirect_url=url_for('index'),
            entity=m.Member,
            template='index.html',
            member_url='.member')

@stjb_app.route('/books', methods=['GET', 'POST'])
def books():
    return directory(
            redirect_url=url_for('books'),
            entity=p.Member,
            template='books.html',
            member_url='.book')

@stjb_app.route("/applications")
def applications():
    apps = db.session.execute(db.select(Application).order_by(Application.signature_date)).scalars()
    return render_template('applications.html', apps=apps)

@stjb_app.route('/application/add', methods=['GET', 'POST'])
def application_add():
    form = ApplicationForm()
    if form.validate_on_submit():
        app = Application(guid=uuid.uuid4())
        form.save_application(app)
        db.session.add(app)
        db.session.commit()
        if form.register.data:
            flash('Please verify new member names and monthly dues, and then press Register')
            return redirect(url_for('application_register', guid=app.guid))
        flash('The application has been saved')
        return redirect(url_for('applications'))
    return render_template( 'application.html', form=form)

@stjb_app.route('/application/<guid>', methods=['GET', 'POST'])
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

def redirect_on_existing_member(guid, applicant):
    if applicant.do_register == 'as_member':
        member = find_member(applicant.en_name_first, applicant.en_name_last)
        if member:
            flash(f'{member.person.full_name_address()} is already a parish member')
            return redirect(url_for('application_register', guid=guid))
    return None

def redirect_on_another_active_marriage(guid, person, spouse):
    breakpoint()
    husband = person if person.gender == 'M' else spouse
    wife = spouse if person.gender == 'M' else person
    # check husband
    marriage = find_active_marriage_of_husband(husband.en_name_first, husband.en_name_last)
    if marriage is not None and (marriage.wife.first != wife.en_name_first or marriage.wife.last != wife.en_name_last):
        flash(f'Active marriage between {marriage.husband.full_name()} and {marriage.wife.full_name()} has been found')
        return redirect(url_for('application_register', guid=guid))
    # check wife
    marriage = find_active_marriage_of_wife(wife.en_name_first, wife.en_name_last)
    if marriage is not None and (marriage.husband.first != husband.en_name_first or marriage.husband.last != husband.en_name_last):
        flash(f'Active marriage between {marriage.husband.full_name()} and {marriage.wife.full_name()} has been found')
        return redirect(url_for('application_register', guid=guid))
    return None

def finalize_registration_and_redirect(app, applicant, applicant_spouse, decisions_data, as_of_date):
    decisions = iter(decisions_data)
    person = Person(app, applicant)
    db_person = find_person(applicant.en_name_first, applicant.en_name_last)
    if db_person:
        if next(decisions) == 'update':
            db_person.update_from(person)
        person = db_person
    else:
        db.session.add(person)
    member = Card(app, person, applicant, as_of_date)
    db.session.add(member)
    if applicant_spouse:
        spouse = Person.make_spouse(app, applicant_spouse)
        db_spouse = find_person(applicant_spouse.en_name_first, applicant_spouse.en_name_last)
        if db_spouse:
            if next(decisions) == 'update':
                db_spouse.update_from(spouse)
            spouse = db_spouse
        else:
            db.session.add(spouse)
        husband = person if person.gender == 'M' else spouse
        wife = spouse if person.gender == 'M' else person
        if not find_active_marriage(husband.first, husband.last, wife.first, wife.last):
            marriage = Marriage(husband, wife)
            db.session.add(marriage)
        if applicant_spouse.do_register == 'as_member':
            spouse_member = Card(app, spouse, applicant_spouse, as_of_date)
            db.session.add(spouse_member)
    db.session.commit()
    return redirect(url_for('member', guid=member.guid))

@stjb_app.route('/application/records_update/<guid>', methods=['GET', 'POST'])
def application_records_update(guid):
    if guid not in session:
        flash('Something went wrong, unable to find application data in the session.')
        return redirect(url_for('application_register', guid=guid))
    app = db.get_or_404(Application, uuid.UUID(guid))
    registration_form = ApplicantsRegistrationForm.make_with_form_data(session[guid])
    applicant = registration_form.applicant()
    spouse = registration_form.spouse()
    form = UpdateDecisionsForm()
    if form.validate_on_submit():
        session.pop(guid)
        return finalize_registration_and_redirect(app, applicant, spouse, form.decisions.data, registration_form.as_of_date.data)
    applicants = []
    db_person = find_person(applicant.en_name_first, applicant.en_name_last)
    if db_person:
        app_person = Person(app, applicant)
        applicants.append((applicant, app_person, db_person))
        form.append_decision()
    if spouse:
        db_spouse = find_person(spouse.en_name_first, spouse.en_name_last)
        if db_spouse:
            app_spouse = Person.make_spouse(app, spouse)
            applicants.append((spouse, app_spouse, db_spouse))
            form.append_decision()
    return render_template('records_update.html', form=form, applicants=applicants)

@stjb_app.route('/application/register/<guid>', methods=['GET', 'POST'])
def application_register(guid):
    app = db.get_or_404(Application, uuid.UUID(guid))
    form = ApplicantsRegistrationForm()
    if form.validate_on_submit():
        session[guid] = request.form
        applicant = form.applicant()
        applicant.gender = app.gender
        redirecting = redirect_on_existing_member(app.guid, applicant)
        if redirecting:
            return redirecting
        applicant_p = find_person(applicant.en_name_first, applicant.en_name_last)
        # check if they differ
        should_redirect_to_records_update = applicant_p is not None
        spouse = form.spouse()
        if spouse:
            redirecting = redirect_on_existing_member(app.guid, spouse)
            if redirecting:
                return redirecting
            redirecting = redirect_on_another_active_marriage(guid, applicant, spouse)
            if redirecting:
                return redirecting
            # check if they differ
            spouse_p = find_person(spouse.en_name_first, spouse.en_name_last)
            should_redirect_to_records_update |= spouse_p is not None
        if should_redirect_to_records_update:
            return redirect(url_for('application_records_update', guid=guid))
        session.pop(guid)
        return finalize_registration_and_redirect(
                app, applicant, spouse,
                [],
                form.as_of_date.data)
    if guid in session:
        form = ApplicantsRegistrationForm.make_with_form_data(session[guid])
        form.validate()
        session.pop(guid)
    else:
        form.consider_loading_application(app)
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

@stjb_app.route('/member/<guid>')
def member(guid):
    connection = stjb.connect(db_path)
    entity = m.Member.find_by_guid(connection, guid)
    if not entity:
        connection.close()
        abort(404)
    entity.load_payments(connection)
    connection.close()
    return render_template('member.html', member=entity)

@stjb_app.route('/book/<guid>')
def book(guid):
    connection = stjb.connect(db_path)
    entity = p.Member.find_by_guid(connection, guid)
    if not entity:
        connection.close()
        abort(404)
    entity.load_payments(connection)
    connection.close()
    return render_template('member.html', member=entity)

@stjb_app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
