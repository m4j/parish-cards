from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod

class PaymentSubDuesForm(FlaskForm):
    payor = StringField('Payor last, first name', validators=[DataRequired()], render_kw={'autofocus': True})
    date = StringField('Payment date', validators=[DataRequired(), ISOYearMonthDayValidator()])
    method = SelectField('Payment method', validators=[DataRequired()])
    identifier = StringField('Check number, credit card authorization, etc...', validators=[Optional()])
    amount = IntegerField('Amount', validators=[DataRequired()])
    paid_from = StringField('Dues period from', validators=[DataRequired(), ISOYearMonthValidator()])
    paid_through = StringField('Dues period through', validators=[DataRequired(), ISOYearMonthValidator()])
    comment = TextAreaField('Comment', validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PaymentSubDuesForm, self).__init__(*args, **kwargs)
        self.method.choices = [(method.method, method.method) for method in db.session.scalars(db.select(PaymentMethod))]

    def load_from(self, payment_sub):
        self.payor.data = payment_sub.payor
        self.date.data = payment_sub.date
        self.method.data = payment_sub.method
        self.amount.data = payment_sub.amount
        self.paid_from.data = payment_sub.paid_from
        self.paid_through.data = payment_sub.paid_through
        self.comment.data = payment_sub.comment

    def save_to(self, payment_sub):
        payment_sub.payor = self.payor.data
        payment_sub.date = self.date.data
        payment_sub.method = self.method.data
        payment_sub.identifier = self.identifier.data if self.identifier.data else None
        payment_sub.amount = self.amount.data
        payment_sub.paid_from = self.paid_from.data
        payment_sub.paid_through = self.paid_through.data
        payment_sub.comment = self.comment.data
