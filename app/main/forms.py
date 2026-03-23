from flask_wtf import FlaskForm
from wtforms import Form
from wtforms import StringField, SubmitField, IntegerField, SelectField, TextAreaField, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError, NumberRange, InputRequired
from ..models import Prosphora, Service, Person, MembershipTermination, find_person, find_prosphora
from ..stjb import get_first_name, get_last_name
from .. import db
import uuid

class SearchForm(FlaskForm):
    search_term = StringField('Search by any part of a name, like "irina", or "Иван", or "mar", or "joh"', 
                            render_kw={
                                'autofocus': True,
                                'autocomplete': 'off',
                                'onfocus': 'this.select()'
                            })
    submit_search = SubmitField('Search')

    def __init__(self, search_label=None, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        if search_label:
            self.search_term.label.text = search_label
            self.search_term.render_kw['placeholder'] = search_label


class ProsphoraForm(FlaskForm):
    last_name = StringField('Last Name', validators=[DataRequired()])
    first_name = StringField('First Name', validators=[Optional()])
    family_name = StringField('Family Name', validators=[Optional()])
    ru_last_name = StringField('Last Name (Russian)', validators=[Optional()])
    ru_first_name = StringField('First Name (Russian)', validators=[Optional()])
    ru_family_name = StringField('Family Name (Russian)', validators=[Optional()])
    person_name = StringField(label=None, validators=[Optional()])
    quantity = IntegerField('Quantity', validators=[InputRequired(), NumberRange(0, 100)], default=1)
    paid_through = StringField('Paid Through', validators=[Optional()])
    liturgy = SelectField('Liturgy', validators=[DataRequired()], choices=[])
    notes = TextAreaField('Notes', validators=[Optional()])
    save_changes = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        obj = kwargs.get('obj', None)
        self.original_guid = obj.guid if obj else None
        super(ProsphoraForm, self).__init__(*args, **kwargs)
        # Populate liturgy choices from Service model
        services = db.session.scalars(
            db.select(Service).order_by(Service.name)
        ).all()
        self.liturgy.choices = [(service.name, service.name) for service in services]

    def validate_last_name(self, field):
        """Validate that the primary key (last_name, first_name) doesn't already exist."""
        new_first_name = self.first_name.data.strip()
        # Check if primary key already exists
        existing = find_prosphora(new_first_name, field.data.strip())
        if existing:
            # If editing, exclude the current record
            if self.original_guid and existing.guid == self.original_guid:
                return
            raise ValidationError('A prosphora entry with this last name and first name already exists.')

    @classmethod
    def load(cls, guid):
        """Load a prosphora entry into the form."""
        prosphora = db.session.scalars(
            db.select(Prosphora).filter_by(guid=uuid.UUID(guid))
        ).first()
        if not prosphora:
            return None
        form = cls(obj=prosphora)
        if prosphora.person:
            form.person_name.data = prosphora.person.full_name()
        else:
            form.person_name.data = None
        return form

    def save(self, guid=None):
        """Save form data to the prosphora entry."""
        if guid:
            # Updating existing prosphora
            prosphora = db.session.scalars(
                db.select(Prosphora).filter_by(guid=uuid.UUID(guid))
            ).first()
            if not prosphora:
                return False
        else:
            # Creating new prosphora
            prosphora = Prosphora()

        # Update fields
        prosphora.last_name = self.last_name.data.strip()
        prosphora.first_name = self.first_name.data.strip()
        prosphora.family_name = self.family_name.data or None
        prosphora.ru_last_name = self.ru_last_name.data or None
        prosphora.ru_first_name = self.ru_first_name.data or None
        prosphora.ru_family_name = self.ru_family_name.data or None
        if self.person_name.data:
            person = find_person(
                get_first_name(self.person_name.data),
                get_last_name(self.person_name.data))
            if person:
                prosphora.person = person
            else:
                prosphora.person = None
        prosphora.quantity = self.quantity.data
        prosphora.paid_through = self.paid_through.data or None
        prosphora.liturgy = self.liturgy.data
        prosphora.notes = self.notes.data or None
        if guid is None:
            db.session.add(prosphora)
        db.session.commit()
        return True


class PersonSubForm(Form):
    """Person fields without submit button; used in PersonForm and PersonEditForm."""
    guid = HiddenField('GUID')
    last = StringField('Last Name', validators=[DataRequired()])
    first = StringField('First Name', validators=[DataRequired()])
    other_name = StringField('Other Name', validators=[Optional()])
    middle_name = StringField('Middle Name', validators=[Optional()])
    maiden_name = StringField('Maiden Name', validators=[Optional()])
    ru_last_name = StringField('Last Name', validators=[Optional()])
    ru_maiden_name = StringField('Maiden Name', validators=[Optional()])
    ru_first_name = StringField('First Name', validators=[Optional()])
    ru_other_name = StringField('Other Name', validators=[Optional()])
    ru_patronymic_name = StringField('Patronymic', validators=[Optional()])
    email = StringField('Email', validators=[Optional()])
    home_phone = StringField('Home Phone', validators=[Optional()])
    mobile_phone = StringField('Mobile Phone', validators=[Optional()])
    work_phone = StringField('Work Phone', validators=[Optional()])
    gender = SelectField(
        'Gender',
        validators=[DataRequired()],
        choices=[('M', 'Male'), ('F', 'Female')]
    )
    address = StringField('Address', validators=[Optional()])
    city = StringField('City', validators=[Optional()])
    state_region = StringField('State / Region', validators=[Optional()])
    postal_code = StringField('Postal Code', validators=[Optional()])
    plus_4 = StringField('Plus 4', validators=[Optional()])
    date_of_birth = StringField('Date of Birth', validators=[Optional()])
    date_of_death = StringField('Date of Death', validators=[Optional()])
    note = TextAreaField('Note', validators=[Optional()])

    # Membership (Card) fields (edited only when Person has an associated Card)
    membership_from = StringField('From', validators=[Optional()])
    membership_through = StringField('End of Membership', validators=[Optional()])
    membership_termination_reason = SelectField('Reason', validators=[Optional()], choices=[])
    dues_amount = IntegerField('Monthly dues', validators=[Optional()])
    dues_paid_through = StringField('Dues Paid Through', validators=[Optional()])
    card_notes = TextAreaField('Notes', validators=[Optional()])

    def __init__(self, *args, **kwargs):
        super(PersonSubForm, self).__init__(*args, **kwargs)
        terminations = db.session.scalars(
            db.select(MembershipTermination).order_by(MembershipTermination.reason)
        ).all()
        self.membership_termination_reason.choices = [('', '—')] + [
            (t.reason, t.reason) for t in terminations
        ]

    def validate_last(self, field):
        if not self.first.data:
            return
        existing = find_person(self.first.data.strip(), field.data.strip())
        if not existing:
            return
        if self.guid.data and existing.guid == uuid.UUID(self.guid.data):
            return
        raise ValidationError('A person with this last name and first name already exists.')

    @property
    def _person(self):
        """Load Person for this subform when guid is present (GET or POST). Used for Card-only rules."""
        if not self.guid.data:
            return None
        return db.session.scalars(db.select(Person).filter_by(guid=uuid.UUID(self.guid.data))).first()

    def validate(self, extra_validators=None):
        if not super(PersonSubForm, self).validate(extra_validators=extra_validators):
            return False
        if self._person and self._person.card:
            return self.validate_membership()
        return True

    def validate_membership(self):
        if not (self.membership_from.data or '').strip():
            self.membership_from.errors.append('Membership start date is required for members.')
            return False
        if not (self.dues_amount.data or 0) > 0:
            self.dues_amount.errors.append('Monthly dues is required for members.')
            return False
        membership_through = (self.membership_through.data or '').strip()
        termination_reason = (self.membership_termination_reason.data or '').strip()
        if membership_through and not termination_reason:
            self.membership_termination_reason.errors.append('Reason is required when membership end date is set.')
            return False
        if not membership_through and termination_reason:
            self.membership_through.errors.append(f'Membership end date is required when reason is "{termination_reason}".')
            return False
        return True

    def apply_to_person(self, person):
        """Write form data to Person (always updates last/first; DB handles FK cascade)."""
        person.last = self.last.data.strip()
        person.first = self.first.data.strip()
        person.other_name = self.other_name.data or None
        person.middle_name = self.middle_name.data or None
        person.maiden_name = self.maiden_name.data or None
        person.ru_last_name = self.ru_last_name.data or None
        person.ru_maiden_name = self.ru_maiden_name.data or None
        person.ru_first_name = self.ru_first_name.data or None
        person.ru_other_name = self.ru_other_name.data or None
        person.ru_patronymic_name = self.ru_patronymic_name.data or None
        person.email = self.email.data or None
        person.home_phone = self.home_phone.data or None
        person.mobile_phone = self.mobile_phone.data or None
        person.work_phone = self.work_phone.data or None
        person.gender = self.gender.data or None
        person.address = self.address.data or None
        person.city = self.city.data or None
        person.state_region = self.state_region.data or None
        person.postal_code = self.postal_code.data or None
        person.plus_4 = self.plus_4.data or None
        person.date_of_birth = self.date_of_birth.data or None
        person.date_of_death = self.date_of_death.data or None
        person.note = self.note.data or None

        # Only update membership if a Card exists for this person.
        if person.card:
            person.card.membership_from = self.membership_from.data or None
            person.card.membership_through = self.membership_through.data or None
            person.card.membership_termination_reason = self.membership_termination_reason.data or None
            person.card.dues_amount = self.dues_amount.data if self.dues_amount.data is not None else None
            person.card.dues_paid_through = self.dues_paid_through.data or None
            person.card.notes = self.card_notes.data or None

    def populate_from_person(self, person, guid_str):
        """Fill subform fields from a Person (and Card when present). Used by PersonForm.load and PersonEditForm.load."""
        self.guid.data = guid_str
        self.last.data = person.last or ''
        self.first.data = person.first or ''
        self.other_name.data = person.other_name or ''
        self.middle_name.data = person.middle_name or ''
        self.maiden_name.data = person.maiden_name or ''
        self.ru_last_name.data = person.ru_last_name or ''
        self.ru_maiden_name.data = person.ru_maiden_name or ''
        self.ru_first_name.data = person.ru_first_name or ''
        self.ru_other_name.data = person.ru_other_name or ''
        self.ru_patronymic_name.data = person.ru_patronymic_name or ''
        self.email.data = person.email or ''
        self.home_phone.data = person.home_phone or ''
        self.mobile_phone.data = person.mobile_phone or ''
        self.work_phone.data = person.work_phone or ''
        self.gender.data = person.gender or ''
        self.address.data = person.address or ''
        self.city.data = person.city or ''
        self.state_region.data = person.state_region or ''
        self.postal_code.data = person.postal_code or ''
        self.plus_4.data = person.plus_4 or ''
        self.date_of_birth.data = person.date_of_birth or ''
        self.date_of_death.data = person.date_of_death or ''
        self.note.data = person.note or ''

        card = person.card
        if card:
            self.membership_from.data = card.membership_from or ''
            self.membership_through.data = card.membership_through or ''
            self.membership_termination_reason.data = card.membership_termination_reason or ''
            self.dues_amount.data = card.dues_amount if card.dues_amount is not None else None
            self.dues_paid_through.data = card.dues_paid_through or ''
            self.card_notes.data = card.notes or ''
        else:
            self.membership_from.data = ''
            self.membership_through.data = ''
            self.membership_termination_reason.data = ''
            self.dues_amount.data = None
            self.dues_paid_through.data = ''
            self.card_notes.data = ''


class PersonForm(PersonSubForm):
    """Single-person form (new or edit without spouse)."""
    save_changes = SubmitField('Save Changes')

    @classmethod
    def load(cls, guid, prefix=None):
        person = db.session.scalars(
            db.select(Person).filter_by(guid=uuid.UUID(guid))
        ).first()
        if not person:
            return None
        kwargs = {'obj': person}
        if prefix:
            kwargs['prefix'] = prefix
        form = cls(**kwargs)
        cls.populate_from_person(form, person, guid)
        return form


    def save(self, guid=None):
        if guid:
            person = db.session.scalars(
                db.select(Person).filter_by(guid=uuid.UUID(guid))
            ).first()
            if not person:
                return False
        else:
            person = Person()
            db.session.add(person)
        self.apply_to_person(person)
        db.session.commit()
        return True


class PersonEditForm(FlaskForm):
    """Combined form for person + spouse with one submit; PK updates allowed (DB cascade)."""
    person = FormField(PersonSubForm)
    spouse = FormField(PersonSubForm)
    save_changes = SubmitField('Save Changes')

    @classmethod
    def load(cls, guid, person, spouse):
        form = cls()
        for subform, p in [(form.person, person), (form.spouse, spouse)]:
            subform.populate_from_person(p, p.guid.hex)
        return form

    def validate(self, extra_validators=None):
        if not super(PersonEditForm, self).validate(extra_validators=extra_validators):
            return False
        p_g = self.person.gender.data
        s_g = self.spouse.gender.data
        if p_g and s_g and p_g == s_g:
            self.spouse.gender.errors.append('Person and spouse must have different gender.')
            return False
        return True

    def save(self, guid):
        person = db.session.scalars(
            db.select(Person).filter_by(guid=uuid.UUID(guid))
        ).first()
        if not person:
            return False
        spouse = person.spouse
        if not spouse:
            return False
        self.person.apply_to_person(person)
        self.spouse.apply_to_person(spouse)
        db.session.commit()
        return True

