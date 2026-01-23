from flask import render_template, abort, session, redirect, url_for, flash, jsonify, request
from .. import stjb
from .. import db
from .. import member as m
from .. import prosphora as p
from . import main
from ..models import Person
from .forms import SearchForm, ProsphoraForm

@main.route('/', methods=['GET', 'POST'])
def index():
    return _directory(
            redirect_url=url_for('.index'),
            entity=m.Member,
            template='index.html',
            member_url='.member',
            edit_url='')

@main.route('/books', methods=['GET', 'POST'])
def books():
    return _directory(
            redirect_url=url_for('.books'),
            entity=p.Member,
            template='books.html',
            member_url='.book',
            edit_url='.book_edit')

def _directory(redirect_url, member_url, entity, template, edit_url):
    form = SearchForm()
    members = []
    if form.validate_on_submit():
        session['search_term'] = form.search_term.data
        return redirect(redirect_url)
    search_term = session.get('search_term')
    if search_term:
        form.search_term.data = search_term
        members = entity.find_all_by_name(search_term)
        if len(members) == 0:
            flash('Nothing found, please try again')
    return render_template(
            template,
            form=form,
            members=members,
            member_url=member_url,
            edit_url=edit_url)

@main.route('/member/<guid>')
def member(guid):
    entity = m.Member.find_by_guid(guid)
    if not entity:
        abort(404)
    return render_template('member.html', member=entity)

@main.route('/book/<guid>')
def book(guid):
    entity = p.Member.find_by_guid(guid)
    if not entity:
        abort(404)
    return render_template('member.html', member=entity)

@main.route('/book/edit', methods=['GET', 'POST'])
@main.route('/book/edit/<guid>', methods=['GET', 'POST'])
def book_edit(guid=None):
    if guid:
        form = ProsphoraForm.load(guid)
    else:
        form = ProsphoraForm()
    if not form:
        abort(404)
    
    if form.validate_on_submit():
        if form.save(guid):
            flash('Prosphora entry successfully updated.')
            return redirect(url_for('.books'))
        else:
            flash('Error updating prosphora entry.', 'error')
    
    return render_template('main/edit_prosphora.html', form=form)

@main.route('/search_people')
def search_people():
    """Search for people by name and return JSON results"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Build the query
    q = db.select(Person)
    if query:
        q = q.filter(
            Person.last.ilike(f'%{query}%') |
            Person.first.ilike(f'%{query}%')
        )
    people = db.session.scalars(q.order_by(Person.last, Person.first).limit(10)).all()
    return jsonify([{'value': person.full_name(), 'text': person.full_name()} for person in people])