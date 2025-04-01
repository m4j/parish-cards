from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField, BooleanField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError
from wtforms.widgets import HiddenInput
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod, PaymentSubMiscCategory
from ..models import PaymentSubDues, PaymentSubProsphora, PaymentSubMisc
from ..models import dues_range_containing_date, prosphora_range_containing_date
import uuid

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
    
    def does_range_with_date_exists(self, field):
        pass

    def validate_paid_from(self, field):
        if field.data > self.paid_through.data:
            raise ValidationError('Invalid date range')
        if self.does_range_with_date_exists(field.data):
            raise ValidationError(f'Date within another paid range')

    def validate_paid_through(self, field):
        if self.paid_from.data > field.data:
            raise ValidationError('Invalid date range')
        if self.does_range_with_date_exists(field.data):
            raise ValidationError(f'Date within another paid range')

class PaymentSubDuesForm(PaymentSubMixin, PaymentRangeSubMixin, Form):
    def does_range_with_date_exists(self, date):
        dues = dues_range_containing_date(
            date,
            self.first_name.data,
            self.last_name.data)
        if dues and self.guid.data:
            return dues.guid != uuid.UUID(self.guid.data)
        else:
            return dues is not None

class PaymentSubProsphoraForm(PaymentSubMixin, PaymentRangeSubMixin, Form):
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    with_twelve_feasts = BooleanField('12 Feasts')

    def does_range_with_date_exists(self, date):
        prosphora = prosphora_range_containing_date(
            date,
            self.first_name.data,
            self.last_name.data)
        if prosphora and self.guid.data:
            return prosphora.guid != uuid.UUID(self.guid.data)
        else:
            return prosphora is not None

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

    def clear_guids(self):
        """Set all sub-payment GUIDs to None"""
        for entry in self.dues_subs.entries:
            entry.form.guid.data = None
        for entry in self.prosphora_subs.entries:
            entry.form.guid.data = None
        for entry in self.misc_subs.entries:
            entry.form.guid.data = None

    def load_from_payment(self, payment):
        """Load data from a Payment object into the form"""
        self.payment.payor.data = payment.payor
        self.payment.date.data = payment.date
        self.payment.method.data = payment.method
        self.payment.identifier.data = payment.identifier
        self.payment.amount.data = payment.amount
        self.payment.comment.data = payment.comment

        # Load sub-payments
        for sub in payment.dues:
            form = PaymentSubDuesForm()
            form.guid.data = sub.guid.hex
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.last_name.data = sub.last_name
            form.first_name.data = sub.first_name
            form.paid_from.data = sub.paid_from
            form.paid_through.data = sub.paid_through
            self.dues_subs.append_entry(form.data)

        for sub in payment.prosphora:
            form = PaymentSubProsphoraForm()
            form.guid.data = sub.guid.hex
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.last_name.data = sub.last_name
            form.first_name.data = sub.first_name
            form.paid_from.data = sub.paid_from
            form.paid_through.data = sub.paid_through
            form.quantity.data = sub.quantity
            form.with_twelve_feasts.data = sub.with_twelve_feasts
            self.prosphora_subs.append_entry(form.data)

        for sub in payment.misc:
            form = PaymentSubMiscForm()
            form.guid.data = sub.guid.hex
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.category.data = sub.category
            self.misc_subs.append_entry(form.data)

    def save_to_payment(self, payment):
        """Save form data to a Payment object"""
        payment.payor = self.payment.payor.data
        payment.date = self.payment.date.data
        payment.method = self.payment.method.data
        payment.identifier = self.payment.identifier.data or None
        payment.amount = self.payment.amount.data
        payment.comment = self.payment.comment.data or None

        # Track existing sub-payments by guid
        existing_dues = {sub.guid.hex: sub for sub in payment.dues}
        existing_prosphora = {sub.guid.hex: sub for sub in payment.prosphora}
        existing_misc = {sub.guid.hex: sub for sub in payment.misc}

        # Update or create dues sub-payments
        payment.dues = []
        for form_data in self.dues_subs.data:
            guid = form_data.get('guid')
            if guid and guid in existing_dues:
                sub = existing_dues[guid]
            else:
                sub = PaymentSubDues()
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment') or None
            sub.last_name = form_data['last_name']
            sub.first_name = form_data['first_name']
            sub.paid_from = form_data['paid_from']
            sub.paid_through = form_data['paid_through']
            payment.dues.append(sub)

        # Update or create prosphora sub-payments
        payment.prosphora = []
        for form_data in self.prosphora_subs.data:
            guid = form_data.get('guid')
            if guid and guid in existing_prosphora:
                sub = existing_prosphora[guid]
            else:
                sub = PaymentSubProsphora()
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment') or None
            sub.last_name = form_data['last_name']
            sub.first_name = form_data['first_name']
            sub.paid_from = form_data['paid_from']
            sub.paid_through = form_data['paid_through']
            sub.quantity = form_data['quantity']
            sub.with_twelve_feasts = form_data['with_twelve_feasts']
            payment.prosphora.append(sub)

        # Update or create misc sub-payments
        payment.misc = []
        for form_data in self.misc_subs.data:
            guid = form_data.get('guid')
            if guid and guid in existing_misc:
                sub = existing_misc[guid]
            else:
                sub = PaymentSubMisc()
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment') or None
            sub.category = form_data['category']
            payment.misc.append(sub) 