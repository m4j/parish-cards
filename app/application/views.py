from flask import render_template, session, redirect, url_for, flash, request, Markup
from .. import db
from . import application
from .forms import ApplicationForm, ApplicantsRegistrationForm, UpdateDecisionsForm
from ..models import Application, Person, Card, Marriage, find_member, find_person, find_active_marriage, find_active_marriage_of_husband, find_active_marriage_of_wife
import uuid

@application.route("/")
def applications():
    apps = db.session.scalars(db.select(Application).order_by(Application.signature_date.desc()))
    return render_template('application/applications.html', apps=apps)

@application.route('/add', methods=['GET', 'POST'])
def application_add():
    form = ApplicationForm()
    if form.validate_on_submit():
        app = Application()
        form.save_application(app)
        db.session.add(app)
        db.session.commit()
        if form.register.data:
            flash('Please verify new member names and monthly dues, and then press Register', 'info')
            return redirect(url_for('.application_register', guid=app.guid))
        flash('The application has been saved')
        return redirect(url_for('.applications'))
    return render_template('application/application.html', form=form)

@application.route('/<guid>', methods=['GET', 'POST'])
def application_edit(guid):
    app = db.get_or_404(Application, uuid.UUID(guid))
    form = ApplicationForm()
    if form.validate_on_submit():
        form.save_application(app)
        db.session.commit()
        if form.save.data:
            flash('The application has been updated')
            return redirect(url_for('.applications'))
        if app.is_registered():
            flash('The application has been processed already.')
            return redirect(url_for('.application_edit', guid=guid))
        if form.register.data:
            flash('Please verify new member names and monthly dues, and then press Register', 'info')
            return redirect(url_for('.application_register', guid=guid))
    form.load_application(app)
    return render_template('application/application.html', app=app, form=form)

def redirect_on_existing_member(guid, applicant):
    if applicant.do_register == 'as_member':
        member = find_member(applicant.en_name_first, applicant.en_name_last)
        if member:
            flash(Markup(f'<b>{member.person.full_name_address()}</b> is already a member of the parish.'), 'danger')
            return redirect(url_for('.application_register', guid=guid))
    return None

def redirect_on_existing_member_reversed_names(guid, applicant):
    if applicant.do_register == 'as_member':
        member = find_member(applicant.en_name_last, applicant.en_name_first)
        if member:
            flash(Markup(f'<b>{member.person.full_name_address()}</b> is already a member of the parish.'), 'danger')
            flash(Markup(f'Please verify first and last names of <b>{applicant.en_name_last}, {applicant.en_name_first}</b>  and do either: <ul><li>Reversed names in the application? — correct here and press <b>Register</b> again</li><li>No change required, all looks good? — press <b>Register</b> again to proceed</li></ul>'), 'danger')
            return redirect(url_for('.application_register', guid=guid))
    return None

def redirect_on_another_active_marriage(guid, applicant_form, spouse_form):
    husband_form = applicant_form if applicant_form.gender == 'M' else spouse_form
    wife_form = spouse_form if applicant_form.gender == 'M' else applicant_form
    # check husband
    marriage = find_active_marriage_of_husband(husband_form.en_name_first, husband_form.en_name_last)
    if marriage is not None and (
            marriage.wife.first.casefold() != wife_form.en_name_first.casefold() or
            marriage.wife.last.casefold() != wife_form.en_name_last.casefold()):
        flash(f'Active marriage between {marriage.husband.full_name()} and {marriage.wife.full_name()} has been found', 'danger')
        return redirect(url_for('.application_register', guid=guid))
    # check wife
    marriage = find_active_marriage_of_wife(wife_form.en_name_first, wife_form.en_name_last)
    if marriage is not None and (
            marriage.husband.first.casefold() != husband_form.en_name_first.casefold() or
            marriage.husband.last.casefold() != husband_form.en_name_last.casefold()):
        flash(f'Active marriage between {marriage.husband.full_name()} and {marriage.wife.full_name()} has been found', 'danger')
        return redirect(url_for('.application_register', guid=guid))
    return None

def finalize_registration_and_redirect(app, applicant, applicant_spouse, decisions_data, as_of_date):
    decisions = iter(decisions_data)
    person = Person(app, applicant)
    member = None
    db_person = find_person(applicant.en_name_first, applicant.en_name_last)
    if db_person:
        if next(decisions) == 'update':
            db_person.update_from(person)
        person = db_person
    else:
        db.session.add(person)
    if applicant.do_register == 'as_member':
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
    if member:
        return redirect(url_for('main.member', guid=member.guid.hex))
    return redirect(url_for('.applications'))

@application.route('/records_update/<guid>', methods=['GET', 'POST'])
def application_records_update(guid):
    if guid not in session:
        flash('Something went wrong, unable to find application data in the session.')
        return redirect(url_for('.application_register', guid=guid))
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
    return render_template('application/records_update.html', form=form, applicants=applicants)

@application.route('/register/<guid>', methods=['GET', 'POST'])
def application_register(guid):
    #breakpoint()
    app = db.get_or_404(Application, uuid.UUID(guid))
    form = ApplicantsRegistrationForm()
    if form.validate_on_submit():
        applicant_warning_rev_key = f'{guid}_applicant_warning_rev'
        spouse_warning_rev_key = f'{guid}_spouse_warning_rev'
        session[guid] = request.form
        applicant = form.applicant()
        applicant.gender = app.gender
        redirecting = redirect_on_existing_member(app.guid, applicant)
        if redirecting:
            return redirecting
        if not session.get(applicant_warning_rev_key):
            redirecting = redirect_on_existing_member_reversed_names(app.guid, applicant)
            if redirecting:
                session[applicant_warning_rev_key] = True
                return redirecting
        applicant_p = find_person(applicant.en_name_first, applicant.en_name_last)
        # check if they differ
        should_redirect_to_records_update = applicant_p is not None
        spouse = form.spouse()
        if spouse:
            redirecting = redirect_on_existing_member(app.guid, spouse)
            if redirecting:
                return redirecting
            if not session.get(spouse_warning_rev_key):
                redirecting = redirect_on_existing_member_reversed_names(app.guid, spouse)
                if redirecting:
                    session[spouse_warning_rev_key] = True
                    return redirecting
            redirecting = redirect_on_another_active_marriage(guid, applicant, spouse)
            if redirecting:
                return redirecting
            # check if they differ
            spouse_p = find_person(spouse.en_name_first, spouse.en_name_last)
            should_redirect_to_records_update |= spouse_p is not None
        session.pop(applicant_warning_rev_key, False)
        session.pop(spouse_warning_rev_key, False)
        if should_redirect_to_records_update:
            return redirect(url_for('.application_records_update', guid=guid))
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
    return render_template('application/register_members.html', form=form)

