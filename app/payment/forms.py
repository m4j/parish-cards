from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional, ValidationError
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod, date_within_other_dues_range

class PaymentMixin:
    payor = StringField('Payor', validators=[DataRequired()], render_kw={'autofocus': True, 'placeholder': 'Last, first name(s)'})
    date = StringField('Date', validators=[DataRequired(), ISOYearMonthDayValidator()])
    method = SelectField('Method', validators=[DataRequired()])
    identifier = StringField('Identifier', render_kw={'placeholder': 'Check number, credit card auth., etc...'})
    amount = IntegerField('Amount', validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(PaymentMixin, self).__init__(*args, **kwargs)
        self.method.choices = [(method.method, method.method) for method in db.session.scalars(db.select(PaymentMethod))]

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Positive number please')

    def validate_identifier(self, field):
        if self.method.data != 'Cash' and field.data.strip() == '':
            raise ValidationError('Other than Cash transactions must have an identifier/authorization/approval code')

class PaymentRangeMixin:

    paid_from = StringField('Range from', validators=[DataRequired(), ISOYearMonthValidator()])
    paid_through = StringField('To', validators=[DataRequired(), ISOYearMonthValidator()])

    def validate_within_other_ranges(self, field):
        pass

    def validate_paid_from(self, field):
        if field.data > self.paid_through.data:
            raise ValidationError('Invalid date range')
        self.validate_within_other_ranges(field)

    def validate_paid_through(self, field):
        if self.paid_from.data > field.data:
            raise ValidationError('Invalid date range')
        self.validate_within_other_ranges(field)

class PaymentSubDuesForm(PaymentMixin, PaymentRangeMixin, FlaskForm):

    def __init__(self, card, *args, **kwargs):
        super(PaymentSubDuesForm, self).__init__(*args, **kwargs)
        self.card = card

    def validate_within_other_ranges(self, field):
        if date_within_other_dues_range(field.data, self.card.first_name, self.card.last_name):
            raise ValidationError(f'Date within another paid range')

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


