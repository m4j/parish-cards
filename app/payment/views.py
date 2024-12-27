from flask import render_template, abort, session, redirect, url_for, flash, Markup
from .. import db
from . import payment
from ..main.forms import SearchForm
from ..models import find_all_payments, Payment, PaymentSubDues
from .forms import PaymentSubDuesForm
import uuid

@payment.route('/', methods=['GET', 'POST'])
def index():
    form = SearchForm()
    payments = []
    if form.validate_on_submit():
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('.index'))
    name = session.get('name')
    if name:
        session['name'] = None
        payments = find_all_payments(name)
        if len(payments) == 0:
            flash('Nothing found, please try again')
        else:
            flash(Markup('Use <span class="glyphicon glyphicon-repeat"></span> to repeat a transaction'))
    return render_template(
            'payment/payments.html',
            form=form,
            payments=payments)

@payment.route('/repeat_dues/<guid>', methods=['GET', 'POST'])
def repeat_dues(guid):
    sub = db.get_or_404(PaymentSubDues, uuid.UUID(guid))
    form = PaymentSubDuesForm()
    if form.validate_on_submit():
        breakpoint()
        new_payment = Payment(
            payor=form.payor.data,
            date=form.date.data,
            method=form.method.data,
            identifier=form.identifier.data if form.identifier.data else None,
            amount=form.amount.data)
        db.session.add(new_payment)

        new_sub = PaymentSubDues(guid=uuid.uuid4())
        form.save_to(new_sub)
        new_sub.card = sub.card
        new_sub.payment = new_payment
        db.session.add(new_sub)

        db.session.commit()
        if form.submit.data:
            flash(f'Added dues payment for {sub.card}')
            return redirect(url_for('.index'))
    form.load_from(sub)
    return render_template('payment/edit_payment_sub_dues.html', member=sub.card, sub=sub, form=form)
