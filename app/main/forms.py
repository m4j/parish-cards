from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, IntegerField, SelectField, TextAreaField, FormField, HiddenField
from wtforms.validators import DataRequired, Optional, ValidationError, NumberRange, InputRequired
from ..models import Prosphora, Service, Person, find_person, find_prosphora
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

    def validate_last(self, field):
        if not self.first.data:
            return
        existing = find_person(self.first.data.strip(), field.data.strip())
        if not existing:
            return
        if self.guid.data and existing.guid == uuid.UUID(self.guid.data):
            return
        raise ValidationError('A person with this last name and first name already exists.')

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
        form.guid.data = guid
        form.last.data = person.last or ''
        form.first.data = person.first or ''
        form.other_name.data = person.other_name or ''
        form.middle_name.data = person.middle_name or ''
        form.maiden_name.data = person.maiden_name or ''
        form.ru_last_name.data = person.ru_last_name or ''
        form.ru_maiden_name.data = person.ru_maiden_name or ''
        form.ru_first_name.data = person.ru_first_name or ''
        form.ru_other_name.data = person.ru_other_name or ''
        form.ru_patronymic_name.data = person.ru_patronymic_name or ''
        form.email.data = person.email or ''
        form.home_phone.data = person.home_phone or ''
        form.mobile_phone.data = person.mobile_phone or ''
        form.work_phone.data = person.work_phone or ''
        form.gender.data = person.gender or ''
        form.address.data = person.address or ''
        form.city.data = person.city or ''
        form.state_region.data = person.state_region or ''
        form.postal_code.data = person.postal_code or ''
        form.plus_4.data = person.plus_4 or ''
        form.date_of_birth.data = person.date_of_birth or ''
        form.date_of_death.data = person.date_of_death or ''
        form.note.data = person.note or ''
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
            subform.guid.data = p.guid.hex
            subform.last.data = p.last or ''
            subform.first.data = p.first or ''
            subform.other_name.data = p.other_name or ''
            subform.middle_name.data = p.middle_name or ''
            subform.maiden_name.data = p.maiden_name or ''
            subform.ru_last_name.data = p.ru_last_name or ''
            subform.ru_maiden_name.data = p.ru_maiden_name or ''
            subform.ru_first_name.data = p.ru_first_name or ''
            subform.ru_other_name.data = p.ru_other_name or ''
            subform.ru_patronymic_name.data = p.ru_patronymic_name or ''
            subform.email.data = p.email or ''
            subform.home_phone.data = p.home_phone or ''
            subform.mobile_phone.data = p.mobile_phone or ''
            subform.work_phone.data = p.work_phone or ''
            subform.gender.data = p.gender or ''
            subform.address.data = p.address or ''
            subform.city.data = p.city or ''
            subform.state_region.data = p.state_region or ''
            subform.postal_code.data = p.postal_code or ''
            subform.plus_4.data = p.plus_4 or ''
            subform.date_of_birth.data = p.date_of_birth or ''
            subform.date_of_death.data = p.date_of_death or ''
            subform.note.data = p.note or ''
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

