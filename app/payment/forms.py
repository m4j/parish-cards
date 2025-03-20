from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField, BooleanField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError
from wtforms.widgets import HiddenInput
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod, PaymentSubMiscCategory
from ..models import PaymentSubDues, PaymentSubProsphora, PaymentSubMisc
from ..models import dues_range_containing_date, prosphora_range_containing_date

class PaymentSubMixin:
    guid = HiddenField('GUID')
    amount = IntegerField('Amount', validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional()])

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Positive number please')

class PaymentRangeSubMixin:
    last_name = StringField('Last Name', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
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

class PaymentSubDuesForm(PaymentSubMixin, PaymentRangeSubMixin, Form):
    def is_date_within_existing_range(self, date):
        return dues_range_containing_date(
            date,
            self.first_name.data,
            self.last_name.data) is not None

class PaymentSubProsphoraForm(PaymentSubMixin, PaymentRangeSubMixin, Form):
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    with_twelve_feasts = BooleanField('12 Feasts')

    def is_date_within_existing_range(self, date):
        return prosphora_range_containing_date(
            date,
            self.first_name.data,
            self.last_name.data) is not None

class PaymentSubMiscForm(PaymentSubMixin, Form):
    category = SelectField('Category', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(PaymentSubMiscForm, self).__init__(*args, **kwargs)
        self.category.choices = [(cat.category, cat.category) for cat in db.session.scalars(db.select(PaymentSubMiscCategory))]

class PaymentBaseForm(Form):
    payor = StringField('Payor', validators=[DataRequired()], render_kw={'autofocus': True, 'placeholder': 'Last, first name(s)'})
    date = StringField('Date', validators=[DataRequired(), ISOYearMonthDayValidator()])
    method = SelectField('Method', validators=[DataRequired()])
    identifier = StringField('Identifier', render_kw={'placeholder': 'Check number, credit card auth., etc...'})
    amount = IntegerField('Amount', validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(PaymentBaseForm, self).__init__(*args, **kwargs)
        self.method.choices = [(method.method, method.display_full) for method in db.session.scalars(db.select(PaymentMethod))]

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Positive number please')

    def validate_identifier(self, field):
        if self.method.data != 'Cash' and field.data.strip() == '':
            method = db.session.scalar(db.select(PaymentMethod).filter(PaymentMethod.method == self.method.data))
            raise ValidationError(f'{method.validation_message} required')

class MultiPaymentForm(FlaskForm):
    payment = FormField(PaymentBaseForm)
    dues_subs = FieldList(FormField(PaymentSubDuesForm), min_entries=0)
    prosphora_subs = FieldList(FormField(PaymentSubProsphoraForm), min_entries=0)
    misc_subs = FieldList(FormField(PaymentSubMiscForm), min_entries=0)
    submit_btn = SubmitField('Submit')

    def load_from_payment(self, payment):
        """Load data from a Payment object into the form"""
        self.payment.payor.data = payment.payor
        self.payment.date.data = payment.date
        self.payment.method.data = payment.method
        self.payment.identifier.data = payment.identifier
        self.payment.amount.data = payment.amount
        self.payment.comment.data = payment.comment

        # Load sub-payments
        for sub in payment.dues_subs:
            form = PaymentSubDuesForm()
            form.guid.data = sub.guid
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.last_name.data = sub.last_name
            form.first_name.data = sub.first_name
            form.paid_from.data = sub.paid_from
            form.paid_through.data = sub.paid_through
            self.dues_subs.append_entry(form.data)

        for sub in payment.prosphora_subs:
            form = PaymentSubProsphoraForm()
            form.guid.data = sub.guid
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.last_name.data = sub.last_name
            form.first_name.data = sub.first_name
            form.paid_from.data = sub.paid_from
            form.paid_through.data = sub.paid_through
            form.quantity.data = sub.quantity
            form.with_twelve_feasts.data = sub.with_twelve_feasts
            self.prosphora_subs.append_entry(form.data)

        for sub in payment.misc_subs:
            form = PaymentSubMiscForm()
            form.guid.data = sub.guid
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.category.data = sub.category
            self.misc_subs.append_entry(form.data)

    def save_to_payment(self, payment):
        """Save form data to a Payment object"""
        payment.payor = self.payment.payor.data
        payment.date = self.payment.date.data
        payment.method = self.payment.method.data
        payment.identifier = self.payment.identifier.data
        payment.amount = self.payment.amount.data
        payment.comment = self.payment.comment.data

        # Track existing sub-payments by guid
        existing_dues = {sub.guid: sub for sub in payment.dues_subs}
        existing_prosphora = {sub.guid: sub for sub in payment.prosphora_subs}
        existing_misc = {sub.guid: sub for sub in payment.misc_subs}

        # Update or create dues sub-payments
        payment.dues_subs = []
        for form_data in self.dues_subs.data:
            guid = form_data.get('guid')
            if guid and guid in existing_dues:
                sub = existing_dues[guid]
            else:
                sub = PaymentSubDues()
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment')
            sub.last_name = form_data['last_name']
            sub.first_name = form_data['first_name']
            sub.paid_from = form_data['paid_from']
            sub.paid_through = form_data['paid_through']
            payment.dues_subs.append(sub)

        # Update or create prosphora sub-payments
        payment.prosphora_subs = []
        for form_data in self.prosphora_subs.data:
            guid = form_data.get('guid')
            if guid and guid in existing_prosphora:
                sub = existing_prosphora[guid]
            else:
                sub = PaymentSubProsphora()
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment')
            sub.last_name = form_data['last_name']
            sub.first_name = form_data['first_name']
            sub.paid_from = form_data['paid_from']
            sub.paid_through = form_data['paid_through']
            sub.quantity = form_data['quantity']
            sub.with_twelve_feasts = form_data['with_twelve_feasts']
            payment.prosphora_subs.append(sub)

        # Update or create misc sub-payments
        payment.misc_subs = []
        for form_data in self.misc_subs.data:
            guid = form_data.get('guid')
            if guid and guid in existing_misc:
                sub = existing_misc[guid]
            else:
                sub = PaymentSubMisc()
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment')
            sub.category = form_data['category']
            payment.misc_subs.append(sub) 