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
        if len(members) == 1:
            return redirect(url_for(member_url, guid=members[0]['GUID']))
    return render_template(
            template,
            form=form,
            members=members,
            member_url=member_url)

@main.route('/member/<guid>')
def member(guid):
    connection = stjb.connect(db_path)
    entity = m.Member.find_by_guid(connection, guid)
    if not entity:
        connection.close()
        abort(404)
    entity.load_payments(connection)
    connection.close()
    return render_template('member.html', member=entity)

@main.route('/book/<guid>')
def book(guid):
    connection = stjb.connect(db_path)
    entity = p.Member.find_by_guid(connection, guid)
    if not entity:
        connection.close()
        abort(404)
    entity.load_payments(connection)
    connection.close()
    return render_template('member.html', member=entity)

