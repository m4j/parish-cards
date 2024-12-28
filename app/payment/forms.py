from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional, ValidationError
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod, find_date_within_any_paid_range

class PaymentSubDuesForm(FlaskForm):
    payor = StringField('Payor last, first name', validators=[DataRequired()], render_kw={'autofocus': True})
    date = StringField('Payment date', validators=[DataRequired(), ISOYearMonthDayValidator()])
    method = SelectField('Payment method', validators=[DataRequired()])
    identifier = StringField('Check number, credit card authorization, etc...')
    amount = IntegerField('Amount', validators=[DataRequired()])
    paid_from = StringField('Dues period from', validators=[DataRequired(), ISOYearMonthValidator()])
    paid_through = StringField('Dues period through', validators=[DataRequired(), ISOYearMonthValidator()])
    comment = TextAreaField('Comment', validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, card, *args, **kwargs):
        super(PaymentSubDuesForm, self).__init__(*args, **kwargs)
        self.method.choices = [(method.method, method.method) for method in db.session.scalars(db.select(PaymentMethod))]
        self.card = card

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
        if self.comment.data:
            payment_sub.comment = self.comment.data

    def validate_identifier(self, field):
        if self.method.data != 'Cash' and field.data.strip() == '':
            raise ValidationError('Non cash transactions must have an identifier')

    def validate_paid_from(self, field):
        if field.data > self.paid_through.data:
            raise ValidationError('Invalid date range')
        if find_date_within_any_paid_range(field.data, self.card.member_first, self.card.member_last):
            raise ValidationError(f'Date {field.data} was already paid for')

    def validate_paid_through(self, field):
        if self.paid_from.data > field.data:
            raise ValidationError('Invalid date range')
        if find_date_within_any_paid_range(field.data, self.card.member_first, self.card.member_last):
            raise ValidationError(f'Date {field.data} was already paid for')


