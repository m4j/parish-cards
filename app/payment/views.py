from flask import render_template, abort, session, redirect, url_for, flash, Markup, request, jsonify
from .. import db
from . import payment
from ..main.forms import SearchForm
from ..models import find_sub_dues_payments, find_sub_prosphora_payments, Payment, PaymentSubDues, PaymentSubProsphora, find_payments_with_multiple_subs, Card, Prosphora
from .forms import PaymentSubDuesForm, PaymentSubProsphoraForm, PaymentSubMiscForm, MultiPaymentForm
import uuid
from collections import namedtuple

TemplateValues = namedtuple('TemplateValues', 'header member_view repeat_payment_view')

_dues_template_values = TemplateValues(
        header='Member Dues Payments',
        member_view='main.member',
        repeat_payment_view='.repeat_dues'
)

_prosphora_template_values = TemplateValues(
        header='Prosphora Payments',
        member_view='main.book',
        repeat_payment_view='.repeat_prosphora'
)

def payments(find_sub_payments, parameters):
    form = SearchForm()
    payments = []
    if form.validate_on_submit():
        session['search_term'] = form.search_term.data
        return redirect(url_for(request.endpoint))
    search_term = session.get('search_term')
    if search_term:
        form.search_term.data = search_term
        payments = find_sub_payments(search_term)
        if len(payments) == 0:
            flash('Nothing found, please try again')
        else:
            flash(Markup('Use <span class="glyphicon glyphicon-repeat"></span> to repeat a transaction'))
    return render_template(
        'payment/payments.html',
        form=form,
        payments=payments,
        parameters=parameters
    )

@payment.route('/dues', methods=['GET', 'POST'])
def dues():
    return payments(find_sub_dues_payments, _dues_template_values)

@payment.route('/prosphora', methods=['GET', 'POST'])
def prosphora():
    return payments(find_sub_prosphora_payments, _prosphora_template_values)

@payment.route('/dues/repeat/<guid>', methods=['GET', 'POST'])
def repeat_dues(guid):
    return repeat_sub_payment(
        guid=guid,
        model=PaymentSubDues,
        sub_form=PaymentSubDuesForm,
        template='payment/edit_payment_dues.html',
        after_submit_url=url_for('.dues')
    )

@payment.route('/prosphora/repeat/<guid>', methods=['GET', 'POST'])
def repeat_prosphora(guid):
    return repeat_sub_payment(
        guid=guid,
        model=PaymentSubProsphora,
        sub_form=PaymentSubProsphoraForm,
        template='payment/edit_payment_prosphora.html',
        after_submit_url=url_for('.prosphora')
    )

def repeat_sub_payment(guid, model, sub_form, template, after_submit_url):
    sub = db.get_or_404(model, uuid.UUID(guid))
    form = sub_form(sub.membership)
    if form.validate_on_submit():
        new_payment = Payment(
            payor=form.payor.data,
            date=form.date.data,
            method=form.method.data,
            identifier=form.identifier.data if form.identifier.data else None,
            amount=form.amount.data)
        db.session.add(new_payment)

        new_sub = model()
        form.save_to(new_sub)
        new_sub.membership = sub.membership
        new_sub.payment = new_payment
        db.session.add(new_sub)

        db.session.commit()
        if form.submit_btn.data:
            flash(f'Added payment for {sub.membership}')
            return redirect(after_submit_url)
    if not form.payor.data:
        form.load_from(sub)
        form.identifier.data = None
    return render_template(
        template,
        member=sub.membership,
        sub=sub,
        form=form)

@payment.route('/add_dues_sub', methods=['POST'])
# @login_required
def add_dues_sub():
    """Handle AJAX request to add a new dues sub-payment form"""
    prefix = request.form.get('_prefix', '')
    form = PaymentSubDuesForm(prefix=f'dues_subs-{prefix}-')
    return render_template('payment/_dues_sub_form.html', subform=form)

@payment.route('/add_prosphora_sub', methods=['POST'])
# @login_required
def add_prosphora_sub():
    """Handle AJAX request to add a new prosphora sub-payment form"""
    prefix = request.form.get('_prefix', '')
    form = PaymentSubProsphoraForm(prefix=f'prosphora_subs-{prefix}-')
    return render_template('payment/_prosphora_sub_form.html', subform=form)

@payment.route('/add_misc_sub', methods=['POST'])
# @login_required
def add_misc_sub():
    """Handle AJAX request to add a new misc sub-payment form"""
    prefix = request.form.get('_prefix', '')
    form = PaymentSubMiscForm(prefix=f'misc_subs-{prefix}-')
    return render_template('payment/_misc_sub_form.html', subform=form)

@payment.route('/multiple_subs', methods=['GET', 'POST'])
# @login_required
def multiple_subs():
    """Display payments with multiple sub-payments"""
    form = SearchForm(search_label='Search by payor, date, method, identifier, amount, or comment')
    payments = []
    
    if form.validate_on_submit():
        session['search_term'] = form.search_term.data
        return redirect(url_for(request.endpoint))
    
    search_term = session.get('search_term')
    if search_term:
        form.search_term.data = search_term
        payments = find_payments_with_multiple_subs(search_term)
        if len(payments) == 0:
            flash('Nothing found, please try again')
    
    return render_template('payment/multiple_subs.html',
                         form=form,
                         payments=payments)

@payment.route('/edit', methods=['GET', 'POST'])
@payment.route('/edit/<guid>', methods=['GET', 'POST'])
def edit_payment(guid=None):
    """Handle creating new payments and editing existing ones"""
    form = MultiPaymentForm()
    payment = None
    
    if guid:
        payment = db.session.scalar(db.select(Payment).filter(Payment.guid == uuid.UUID(guid)))
        if not payment:
            abort(404)
    
    if form.validate_on_submit():
        if not payment:
            payment = Payment()
            payment.guid = uuid.uuid4()
            db.session.add(payment)
        
        form.save_to_payment(payment)
        db.session.commit()
        
        flash('Payment saved successfully')
        return redirect(url_for('.multiple_subs'))
        
    if guid and not form.submit_btn.data:
        form.load_from_payment(payment)
    return render_template('payment/edit_payment.html',
                         form=form,
                         payment=payment)

@payment.route('/repeat/<guid>', methods=['GET', 'POST'])
def repeat_payment(guid):
    """Clone existing payment and edit the clone"""
    payment = db.session.scalar(db.select(Payment).filter(Payment.guid == uuid.UUID(guid)))
    if not payment:
        abort(404)
    form = MultiPaymentForm()
    if form.validate_on_submit():
        new_payment = Payment()
        new_payment.guid = uuid.uuid4()
        form.save_to_payment(new_payment)
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment repeated successfully')
        return redirect(url_for('.multiple_subs'))
    if not form.submit_btn.data:
        form.load_from_payment(payment)
        form.payment.identifier.data = None
        form.payment.date.data = None
        form.clear_guids()
    return render_template('payment/edit_payment.html',
                         form=form,
                         payment=payment)

@payment.route('/search_cards')
def search_cards():
    """Search for cards by name and return JSON results"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Build the query
    q = db.select(Card)
    if query:
        q = q.filter(
            (Card.last_name.ilike(f'%{query}%')) |
            (Card.first_name.ilike(f'%{query}%')) |
            (Card.other_name.ilike(f'%{query}%')) |
            (Card.middle_name.ilike(f'%{query}%')) |
            (Card.maiden_name.ilike(f'%{query}%')) |
            (Card.ru_last_name.ilike(f'%{query}%')) |
            (Card.ru_maiden_name.ilike(f'%{query}%')) |
            (Card.ru_first_name.ilike(f'%{query}%')) |
            (Card.ru_other_name.ilike(f'%{query}%')) |
            (Card.ru_patronymic_name.ilike(f'%{query}%'))
        )
    
    # Limit results and order by name
    cards = db.session.scalars(q.order_by(Card.last_name, Card.first_name).limit(10)).all()
    
    # Format results for Selectize
    results = []
    for card in cards:
        full_name = f"{card.last_name}, {card.first_name}"
        results.append({
            'value': full_name,
            'text': str(card)
        })
    
    return jsonify(results)

@payment.route('/search_prosphora')
def search_prosphora():
    """Search for prosphora entries by name and return JSON results"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Build the query
    q = db.select(Prosphora)
    if query:
        q = q.filter(
            (Prosphora.last_name.ilike(f'%{query}%')) |
            (Prosphora.first_name.ilike(f'%{query}%')) |
            (Prosphora.family_name.ilike(f'%{query}%')) |
            (Prosphora.ru_last_name.ilike(f'%{query}%')) |
            (Prosphora.ru_first_name.ilike(f'%{query}%')) |
            (Prosphora.ru_family_name.ilike(f'%{query}%')) |
            (Prosphora.p_last_name.ilike(f'%{query}%')) |
            (Prosphora.p_first_name.ilike(f'%{query}%'))
        )
    
    # Limit results and order by name
    prosphora_entries = db.session.scalars(q.order_by(Prosphora.last_name, Prosphora.first_name).limit(10)).all()
    
    # Format results for Selectize
    results = []
    for entry in prosphora_entries:
        full_name = f"{entry.last_name}, {entry.first_name}"
        results.append({
            'value': full_name,
            'text': str(entry)
        })
    
    return jsonify(results)
