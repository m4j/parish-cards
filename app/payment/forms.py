from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Optional, ValidationError
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod, dues_range_containing_date, prosphora_range_containing_date

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
        self.method.choices = [(method.method, method.display_full) for method in db.session.scalars(db.select(PaymentMethod))]

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Positive number please')

    def validate_identifier(self, field):
        if self.method.data != 'Cash' and field.data.strip() == '':
            method = db.session.scalar(db.select(PaymentMethod).filter(PaymentMethod.method == self.method.data))
            raise ValidationError(f'{method.validation_message} required')

    def load_from(self, payment_sub):
        self.payor.data = payment_sub.payor
        self.date.data = payment_sub.date
        self.method.data = payment_sub.method
        self.amount.data = payment_sub.amount
        self.comment.data = payment_sub.comment

    def save_to(self, payment_sub):
        payment_sub.payor = self.payor.data
        payment_sub.date = self.date.data
        payment_sub.method = self.method.data
        if self.identifier.data:
            payment_sub.identifier = self.identifier.data
        payment_sub.amount = self.amount.data
        if self.comment.data:
            payment_sub.comment = self.comment.data

class PaymentRangeMixin:

    paid_from = StringField('Range from', validators=[DataRequired(), ISOYearMonthValidator()])
    paid_through = StringField('To', validators=[DataRequired(), ISOYearMonthValidator()])

    def is_date_within_existing_range(self, field):
        pass

    def validate_paid_from(self, field):
        if field.data > self.paid_through.data:
            raise ValidationError('Invalid date range')
        if self.is_date_within_existing_range(field.data):
            raise ValidationError(f'Date within another paid range')

    def validate_paid_through(self, field):
        if self.paid_from.data > field.data:
            raise ValidationError('Invalid date range')
        if self.is_date_within_existing_range(field.data):
            raise ValidationError(f'Date within another paid range')

    def load_from(self, payment_sub):
        self.paid_from.data = payment_sub.paid_from
        self.paid_through.data = payment_sub.paid_through

    def save_to(self, payment_sub):
        payment_sub.paid_from = self.paid_from.data
        payment_sub.paid_through = self.paid_through.data

class PaymentSubDuesForm(PaymentMixin, PaymentRangeMixin, FlaskForm):

    def __init__(self, card, *args, **kwargs):
        super(PaymentSubDuesForm, self).__init__(*args, **kwargs)
        self.membership = card

    def is_date_within_existing_range(self, date):
        return dues_range_containing_date(
            date,
            self.membership.first_name,
            self.membership.last_name) is not None

    def load_from(self, payment_sub):
        PaymentMixin.load_from(self, payment_sub)
        PaymentRangeMixin.load_from(self, payment_sub)

    def save_to(self, payment_sub):
        PaymentMixin.save_to(self, payment_sub)
        PaymentRangeMixin.save_to(self, payment_sub)

class PaymentSubProsphoraForm(PaymentMixin, PaymentRangeMixin, FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    with_twelve_feasts = BooleanField('12 Feasts')

    def __init__(self, prosphora, *args, **kwargs):
        super(PaymentSubProsphoraForm, self).__init__(*args, **kwargs)
        self.membership = prosphora

    def is_date_within_existing_range(self, date):
        return prosphora_range_containing_date(
            date,
            self.membership.first_name,
            self.membership.last_name) is not None

    def load_from(self, payment_sub):
        PaymentMixin.load_from(self, payment_sub)
        PaymentRangeMixin.load_from(self, payment_sub)
        self.quantity.data = payment_sub.quantity
        self.with_twelve_feasts.data = payment_sub.with_twelve_feasts

    def save_to(self, payment_sub):
        PaymentMixin.save_to(self, payment_sub)
        PaymentRangeMixin.save_to(self, payment_sub)
        payment_sub.quantity = self.quantity.data
        payment_sub.with_twelve_feasts = self.with_twelve_feasts.data
