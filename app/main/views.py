from flask import render_template, abort, session, redirect, url_for, flash
from .. import stjb
from .. import db_path
from .. import member as m
from .. import prosphora as p
from . import main
from .forms import SearchForm

@main.route('/', methods=['GET', 'POST'])
def index():
    return _directory(
            redirect_url=url_for('.index'),
            entity=m.Member,
            template='index.html',
            member_url='.member')

@main.route('/books', methods=['GET', 'POST'])
def books():
    return _directory(
            redirect_url=url_for('.books'),
            entity=p.Member,
            template='books.html',
            member_url='.book')

def _directory(redirect_url, member_url, entity, template):
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
            member_url=member_url)

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

