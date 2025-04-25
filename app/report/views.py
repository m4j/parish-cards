from flask import render_template, request, redirect, url_for, session
from app.report import report
from app.main.forms import SearchForm
from app.models import find_record_sheets, find_payments_by_record_id

@report.route('/record_sheets', methods=['GET', 'POST'])
def index():
    form = SearchForm(search_label='Search by identifier, date, or description')
    results = []
    
    if form.validate_on_submit():
        session['search_term'] = form.search_term.data
        return redirect(url_for(request.endpoint))
    
    search_term = session.get('search_term')
    if search_term:
        form.search_term.data = search_term
        results = find_record_sheets(search_term) if search_term else []
    
    return render_template('report/record_sheets.html', form=form, results=results, search_term=search_term)

@report.route('/record_sheet_payments')
def get_record_sheet_payments():
    record_id = request.args.get('record_id')
    if not record_id:
        return render_template('report/_record_sheet_payments.html', payments=[])
    
    payments = find_payments_by_record_id(record_id)
    return render_template('report/_record_sheet_payments.html', payments=payments)
