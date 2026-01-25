from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField, BooleanField, FieldList, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError
from wtforms.widgets import HiddenInput
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator
from .. import db
from ..models import PaymentMethod, PaymentSubMiscCategory
from ..models import PaymentSubDues, PaymentSubProsphora, PaymentSubMisc
from ..models import dues_range_containing_date, prosphora_range_containing_date, find_prosphora
from ..stjb import get_first_name, get_last_name
import uuid

class PaymentSubMixin:
    guid = HiddenField('GUID')
    amount = IntegerField('Amount', validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional()])

    def validate_amount(self, field):
        if field.data <= 0:
            raise ValidationError('Positive number please')

class PaymentRangeSubMixin:
    member_name = StringField(label=None, validators=[DataRequired()])
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

    def get_last_name(self):
        return get_last_name(self.member_name.data)

    def get_first_name(self):
        return get_first_name(self.member_name.data)

class PaymentSubDuesForm(PaymentSubMixin, PaymentRangeSubMixin, Form):
    def does_range_with_date_exists(self, date):
        dues = dues_range_containing_date(
            date,
            self.get_first_name(),
            self.get_last_name())
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
            self.get_first_name(),
            self.get_last_name())
        if prosphora and self.guid.data:
            return prosphora.guid != uuid.UUID(self.guid.data)
        else:
            return prosphora is not None

    def validate_quantity(self, field):
        if field.data <= 0:
            raise ValidationError('Positive number please')

class PaymentSubMiscForm(PaymentSubMixin, Form):
    category = SelectField('Category', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(PaymentSubMiscForm, self).__init__(*args, **kwargs)
        self.category.choices = [(cat.category, cat.category) for cat in db.session.scalars(db.select(PaymentSubMiscCategory))]

class PaymentBaseForm(Form):
    guid = HiddenField('GUID')
    payor = StringField('Payor', validators=[DataRequired()], render_kw={'autofocus': True, 'placeholder': 'Last, first name(s)'})
    date = StringField('Date', validators=[DataRequired(), ISOYearMonthDayValidator()], render_kw={'placeholder': 'Date on the check, credit card slip, etc...'})
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

    def validate_total_amount(self, dues_subs, prosphora_subs, misc_subs):
        """Validate that the total of all sub-payments equals the payment amount"""
        total = 0
        amounts = []
        
        for sub in dues_subs:
            amounts.append(f"dues:{sub.form.amount.data}")
            total += sub.form.amount.data
            
        for sub in prosphora_subs:
            amounts.append(f"prosphora:{sub.form.amount.data}")
            total += sub.form.amount.data
            
        for sub in misc_subs:
            amounts.append(f"misc:{sub.form.amount.data}")
            total += sub.form.amount.data
            
        if total != self.amount.data:
            breakdown = " + ".join(amounts) if amounts else "0"
            raise ValidationError(f'Total of sub-payments ({breakdown} = {total}) does not equal payment amount ({self.amount.data})')

class MultiPaymentForm(FlaskForm):
    payment = FormField(PaymentBaseForm)
    dues_subs = FieldList(FormField(PaymentSubDuesForm), min_entries=0)
    prosphora_subs = FieldList(FormField(PaymentSubProsphoraForm), min_entries=0)
    misc_subs = FieldList(FormField(PaymentSubMiscForm), min_entries=0)
    submit_btn = SubmitField('Submit')

    def clear_guids(self):
        """Set all sub-payment GUIDs to None"""
        self.payment.guid.data = None
        for entry in self.dues_subs.entries:
            entry.form.guid.data = None
        for entry in self.prosphora_subs.entries:
            entry.form.guid.data = None
        for entry in self.misc_subs.entries:
            entry.form.guid.data = None

    def load_from_payment(self, payment):
        """Load data from a Payment object into the form"""
        self.payment.guid.data = payment.guid.hex
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
            form.member_name.data = sub.full_name()
            form.paid_from.data = sub.paid_from
            form.paid_through.data = sub.paid_through
            self.dues_subs.append_entry(form.data)

        for sub in payment.prosphora:
            form = PaymentSubProsphoraForm()
            form.guid.data = sub.guid.hex
            form.amount.data = sub.amount
            form.comment.data = sub.comment
            form.member_name.data = sub.full_name()
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
        payment.identifier = self.payment.identifier.data.strip()
        payment.amount = self.payment.amount.data
        payment.comment = self.payment.comment.data or None

        # Track existing sub-payments by guid
        existing_dues = {sub.guid.hex: sub for sub in payment.dues}
        existing_prosphora = {sub.guid.hex: sub for sub in payment.prosphora}
        existing_misc = {sub.guid.hex: sub for sub in payment.misc}

        for dues in payment.dues:
            if dues.guid.hex not in [entry.form.guid.data for entry in self.dues_subs]:
                payment.dues.remove(dues)

        for prosphora in payment.prosphora:
            if prosphora.guid.hex not in [entry.form.guid.data for entry in self.prosphora_subs]:
                payment.prosphora.remove(prosphora)

        for misc in payment.misc:
            if misc.guid.hex not in [entry.form.guid.data for entry in self.misc_subs]:
                payment.misc.remove(misc)

        for entry in self.dues_subs:
            form_data = entry.form.data
            guid = form_data.get('guid')
            if guid and guid in existing_dues:
                sub = existing_dues[guid]
            else:
                sub = PaymentSubDues()
                payment.dues.append(sub)
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment') or None
            sub.last_name = entry.form.get_last_name() or ''    # FIXME: use person
            sub.first_name = entry.form.get_first_name() or ''
            sub.paid_from = form_data['paid_from']
            sub.paid_through = form_data['paid_through']

        for entry in self.prosphora_subs:
            form_data = entry.form.data
            guid = form_data.get('guid')
            if guid and guid in existing_prosphora:
                sub = existing_prosphora[guid]
            else:
                sub = PaymentSubProsphora()
                payment.prosphora.append(sub)
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment') or None
            prosphora = find_prosphora(entry.form.get_first_name() or '', entry.form.get_last_name() or '')
            if prosphora is not None:
                sub.membership = prosphora
            sub.paid_from = form_data['paid_from']
            sub.paid_through = form_data['paid_through']
            sub.quantity = form_data['quantity']
            sub.with_twelve_feasts = form_data['with_twelve_feasts']

        for entry in self.misc_subs:
            form_data = entry.form.data
            guid = form_data.get('guid')
            if guid and guid in existing_misc:
                sub = existing_misc[guid]
            else:
                sub = PaymentSubMisc()
                payment.misc.append(sub)
                
            sub.amount = form_data['amount']
            sub.comment = form_data.get('comment') or None
            sub.category = form_data['category']

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False
            
        try:
            self.payment.validate_total_amount(self.dues_subs, self.prosphora_subs, self.misc_subs)
            return True
        except ValidationError as e:
            self.payment.amount.errors.append(str(e))
            return False 
