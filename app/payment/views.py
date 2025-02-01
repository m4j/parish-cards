from flask import render_template, abort, session, redirect, url_for, flash, Markup, request
from .. import db
from . import payment
from ..main.forms import SearchForm
from ..models import find_sub_dues_payments, find_sub_prosphora_payments, Payment, PaymentSubDues
from .forms import PaymentSubDuesForm
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
        repeat_payment_view='.repeat_dues'
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
    sub = db.get_or_404(PaymentSubDues, uuid.UUID(guid))
    form = PaymentSubDuesForm(sub.membership)
    if form.validate_on_submit():
        new_payment = Payment(
            payor=form.payor.data,
            date=form.date.data,
            method=form.method.data,
            identifier=form.identifier.data if form.identifier.data else None,
            amount=form.amount.data)
        db.session.add(new_payment)

        new_sub = PaymentSubDues(guid=uuid.uuid4())
        form.save_to(new_sub)
        new_sub.membership = sub.membership
        new_sub.payment = new_payment
        db.session.add(new_sub)

        db.session.commit()
        if form.submit.data:
            flash(f'Added dues payment for {sub.membership}')
            return redirect(url_for('.dues'))
    if not form.payor.data:
        form.load_from(sub)
    return render_template(
        'payment/edit_payment_dues.html',
        member=sub.membership,
        sub=sub,
        form=form)
