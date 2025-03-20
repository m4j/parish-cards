from flask import render_template, abort, session, redirect, url_for, flash, Markup, request
from .. import db
from . import payment
from ..main.forms import SearchForm
from ..models import find_sub_dues_payments, find_sub_prosphora_payments, Payment, PaymentSubDues, PaymentSubProsphora, find_payments_with_multiple_subs
from .forms import PaymentSubDuesForm, PaymentSubProsphoraForm, PaymentSubMiscForm
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
    form = PaymentSubDuesForm()
    return render_template('payment/_dues_sub_form.html', form=form)

@payment.route('/add_prosphora_sub', methods=['POST'])
# @login_required
def add_prosphora_sub():
    """Handle AJAX request to add a new prosphora sub-payment form"""
    form = PaymentSubProsphoraForm()
    return render_template('payment/_prosphora_sub_form.html', form=form)

@payment.route('/add_misc_sub', methods=['POST'])
# @login_required
def add_misc_sub():
    """Handle AJAX request to add a new misc sub-payment form"""
    form = PaymentSubMiscForm()
    return render_template('payment/_misc_sub_form.html', form=form)

@payment.route('/multiple_subs', methods=['GET', 'POST'])
# @login_required
def multiple_subs():
    """Display payments with multiple sub-payments"""
    form = SearchForm()
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
