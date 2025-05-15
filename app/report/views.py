from flask import render_template, request, redirect, url_for, session, flash, abort
from app.report import report
from app.main.forms import SearchForm
from app.models import find_record_sheets, find_payments_by_record_id, RecordSheet, db, delete_record_sheet
from .forms import RecordSheetForm

@report.route('/record_sheets', methods=['GET', 'POST'])
def index():
    form = SearchForm(search_label='Search by identifier, date, payor or description')
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

@report.route('/record_sheet/edit', methods=['GET', 'POST'])
@report.route('/record_sheet/edit/<record_id>', methods=['GET', 'POST'])
def edit_record_sheet(record_id=None):
    record_sheet = None
    if record_id == '9999-12-31':
        flash('Cannot edit default record sheet.', 'error')
        return redirect(url_for('.record_sheets'))
    if record_id:
        record_sheet = db.session.get(RecordSheet, record_id)
        if not record_sheet:
            abort(404)
    form = RecordSheetForm(obj=record_sheet)
        
    if form.validate_on_submit():
        if not record_sheet:
            record_sheet = RecordSheet()
            record_sheet.identifier = record_id
            db.session.add(record_sheet)
        if form.populate_obj(record_sheet):
            flash('Record sheet updated successfully.')
            return redirect(url_for('.record_sheets'))
        else:
            flash('Error updating record sheet.', 'error')
            abort(404)
        
    return render_template('report/edit_record_sheet.html',
                         form=form,
                         record_sheet=record_sheet,
                         payments=record_sheet.payments if record_sheet else [])

@report.route('/record_sheet/<record_id>/delete', methods=['POST'])
def delete_record_sheet(record_id):
    if record_id == '9999-12-31':
        flash('Cannot delete default record sheet.', 'error')
        return redirect(url_for('.record_sheets'))
        
    try:
        if delete_record_sheet(record_id):
            flash('Record sheet deleted successfully.')
        else:
            flash('Record sheet not found.', 'error')
    except Exception as e:
        flash(f'Error deleting record sheet: {str(e)}', 'error')
        
    return redirect(url_for('.record_sheets'))
