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
        session['search_term'] = form.search_term.data
        return redirect(url_for('.index'))
    search_term = session.get('search_term')
    if search_term:
        form.search_term.data = search_term
        payments = find_all_payments(search_term)
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
    form = PaymentSubDuesForm(sub.card)
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
        new_sub.card = sub.card
        new_sub.payment = new_payment
        db.session.add(new_sub)

        db.session.commit()
        if form.submit.data:
            flash(f'Added dues payment for {sub.card}')
            return redirect(url_for('.index'))
    if not form.payor.data:
        form.load_from(sub)
    return render_template('payment/edit_payment_sub_dues.html', member=sub.card, sub=sub, form=form)
