from .forms import RecordSheetForm
from app.latex import compile_latex_to_pdf
from app.latex import jinja_latex_env, escape_special_latex_characters, md_to_latex
from app.main.forms import SearchForm
from app.models import find_record_sheets, RecordSheet, db, delete_record_sheet, Payment, find_payments_by_record_id
from app.report import report
from flask import render_template, request, redirect, url_for, session, flash, abort, Response, jsonify, current_app
from sqlalchemy import text
import base64
import datetime
import os
import shutil
import subprocess
import tempfile
import uuid
import logging

logger = logging.getLogger(__name__)

@report.route('/record_sheets', methods=['GET', 'POST'])
def record_sheets():
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
        return render_template('report/_record_sheet_payments.html', payments=[], show_checkboxes=False)
    
    payments = find_payments_by_record_id(record_id)
    return render_template('report/_record_sheet_payments.html', payments=payments, show_checkboxes=False)

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
            db.session.add(record_sheet)
            
        form.populate_obj(record_sheet)
        # Get selected payments from form
        selected_payments = []
        if form.selected_payments.data:
            uuids = [uuid.UUID(guid) for guid in form.selected_payments.data]
            selected_payments = db.session.scalars(
                db.select(Payment).filter(Payment.guid.in_(uuids))
            ).all()
        # Move deselected payments to the default record sheet
        removed_payments = set(record_sheet.payments) - set(selected_payments)
        default_record_sheet = db.session.get(RecordSheet, '9999-12-31')
        for payment in removed_payments:
            payment.record_sheet = default_record_sheet
        for payment in selected_payments:
            payment.record_sheet = record_sheet
        db.session.commit()
        
        flash('Record sheet successfully created.' if not record_id else 'Record sheet successfully updated.')
        return redirect(url_for('.record_sheets'))
        
    return render_template('report/edit_record_sheet.html',
                         form=form,
                         record_sheet=record_sheet,
                         payments=record_sheet.payments if record_sheet else find_payments_by_record_id('9999-12-31'))

@report.route('/record_sheet/<record_id>/delete', methods=['POST'])
def record_sheet_delete(record_id):
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

@report.route('/record_sheet/<record_id>/print_ajax')
def generate_record_sheet_pdf_ajax(record_id):
    """
    Generate PDF for a record sheet using the poop_sheet.tex template and XeLaTeX.
    
    This route:
    1. Retrieves the record sheet
    2. Queries the payment_sheet_v database view for all payment data
    3. Generates LaTeX using the custom Jinja environment with LaTeX-specific delimiters
    4. Compiles the LaTeX to PDF using XeLaTeX
    5. Returns the PDF data as base64 encoded JSON for client-side blob creation and display
    
    Args:
        record_id (str): The record sheet identifier
        
    Returns:
        dict: JSON response with base64 encoded PDF data and filename, or error message
    """
    try:
        # Get the record sheet
        record_sheet = db.session.get(RecordSheet, record_id)
        if not record_sheet:
            return {'error': 'Record sheet not found'}, 404
        
        # Get data from the payment_sheet_v database view
        result = db.session.execute(
            text('SELECT * FROM payment_sheet_v WHERE record_id = :record_id'),
            {'record_id': record_id}
        )
        
        # Convert the result to a list of dictionaries
        data = []
        for row in result:
            row_dict = dict(row._mapping)
            row_dict_strings = {k: str(v or '') for k, v in row_dict.items()}
            # Convert markdown to LaTeX, but only for the purpose field
            row_dict_strings['purpose'] = md_to_latex(row_dict_strings['purpose'])
            # Escape special LaTeX characters
            data.append(escape_special_latex_characters(row_dict_strings))
        
        if not data:
            return {'error': 'No payments found for this record sheet'}, 400
        
        # Generate LaTeX using the custom Jinja environment
        try:
            template = jinja_latex_env.get_template('poop_sheet.tex')
            latex_content = template.render(
                data=data,
                description=record_sheet.description or '',
                date=datetime.datetime.fromisoformat(record_sheet.date).strftime('%d%b%Y').upper(),
            )
        except Exception as e:
            logger.error(f'Error generating LaTeX for record sheet {record_id}: {str(e)}', exc_info=True)
            return {'error': f'Error generating LaTeX: {str(e)}'}, 500
        
        # Create a temporary directory for LaTeX compilation
        temp_dir = tempfile.mkdtemp()
        logger.info(f'Created temporary directory for LaTeX compilation: {temp_dir}')
        
        tex_file = os.path.join(temp_dir, f'record_sheet_{record_id}.tex')
        
        try:
            # Write LaTeX content to temporary file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF using the helper function
            pdf_content = compile_latex_to_pdf(tex_file, f'record_sheet_{record_id}.pdf')
            
            # Encode PDF as base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Return base64 encoded PDF data
            return {
                'pdf_data': pdf_base64,
                'filename': f'record_sheet_{record_id}.pdf'
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f'PDF compilation timed out for record sheet {record_id}', exc_info=True)
            return {'error': 'PDF compilation timed out'}, 500
        except subprocess.CalledProcessError as e:
            logger.error(f'Error compiling PDF for record sheet {record_id}: {e.stderr}', exc_info=True)
            return {'error': f'Error compiling PDF: {e.stderr}'}, 500
        except FileNotFoundError as e:
            logger.error(f'File not found during PDF compilation for record sheet {record_id}: {str(e)}', exc_info=True)
            return {'error': str(e)}, 500
        except Exception as e:
            logger.error(f'Error during PDF compilation for record sheet {record_id}: {str(e)}', exc_info=True)
            return {'error': f'Error during PDF compilation: {str(e)}'}, 500
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore cleanup errors
    except Exception as e:
        logger.error(f'Error in generate_record_sheet_pdf_ajax route for record_id {record_id}: {str(e)}', exc_info=True)
        return {'error': f'An unexpected error occurred: {str(e)}'}, 500

@report.route('/prosphora/print_ajax')
def generate_prosphora_pdf_ajax():
    """
    Generate PDF for prosphora data using the prosphoras.tex template and XeLaTeX.
    
    This route:
    1. Queries the prosphora_current_v database view for all prosphora data
    2. Generates LaTeX using the custom Jinja environment with LaTeX-specific delimiters
    3. Compiles the LaTeX to PDF using XeLaTeX
    4. Returns the PDF data as base64 encoded JSON for client-side blob creation and display
    
    Returns:
        dict: JSON response with base64 encoded PDF data and filename, or error message
    """
    try:
        # Get data from the prosphora_current_v database view
        result = db.session.execute(
            text('SELECT * FROM prosphora_current_v ORDER BY name')
        )
        
        # Convert the result to a list of dictionaries
        data = []
        for row in result:
            row_dict = dict(row._mapping)
            row_dict_strings = {k: str(v or '') for k, v in row_dict.items()}
            # Escape special LaTeX characters
            data.append(escape_special_latex_characters(row_dict_strings))
        
        if not data:
            return {'error': 'No prosphora data found'}, 400
        
        # Generate LaTeX using the custom Jinja environment
        try:
            template = jinja_latex_env.get_template('prosphoras.tex')
            latex_content = template.render(data=data)
        except Exception as e:
            logger.error(f'Error generating LaTeX for prosphora PDF: {str(e)}', exc_info=True)
            return {'error': f'Error generating LaTeX: {str(e)}'}, 500
        
        # Create a temporary directory for LaTeX compilation
        temp_dir = tempfile.mkdtemp()
        tex_file = os.path.join(temp_dir, 'prosphoras.tex')
        
        try:
            # Write LaTeX content to temporary file
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF using the helper function
            pdf_content = compile_latex_to_pdf(tex_file, 'prosphoras.pdf')
            
            # Encode PDF as base64
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Return base64 encoded PDF data
            return {
                'pdf_data': pdf_base64,
                'filename': 'prosphoras.pdf'
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f'PDF compilation timed out for prosphora PDF', exc_info=True)
            return {'error': 'PDF compilation timed out'}, 500
        except subprocess.CalledProcessError as e:
            logger.error(f'Error compiling PDF for prosphora: {e.stderr}', exc_info=True)
            return {'error': f'Error compiling PDF: {e.stderr}'}, 500
        except FileNotFoundError as e:
            logger.error(f'File not found during PDF compilation for prosphora: {str(e)}', exc_info=True)
            return {'error': str(e)}, 500
        except Exception as e:
            logger.error(f'Error during PDF compilation for prosphora: {str(e)}', exc_info=True)
            return {'error': f'Error during PDF compilation: {str(e)}'}, 500
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass  # Ignore cleanup errors
    except Exception as e:
        logger.error(f'Error in generate_prosphora_pdf_ajax route: {str(e)}', exc_info=True)
        return {'error': f'An unexpected error occurred: {str(e)}'}, 500
