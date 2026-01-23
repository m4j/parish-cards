from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional, ValidationError
from ..models import Prosphora, Service, find_person
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
    quantity = IntegerField('Quantity', validators=[DataRequired()], default=1)
    paid_through = StringField('Paid Through', validators=[Optional()])
    liturgy = SelectField('Liturgy', validators=[DataRequired()], choices=[])
    notes = TextAreaField('Notes', validators=[Optional()])
    save_changes = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        obj = kwargs.get('obj', None)
        self.original_guid = obj.guid if obj else None
        self.original_last_name = obj.last_name if obj else None
        self.original_first_name = obj.first_name if obj else None
        super(ProsphoraForm, self).__init__(*args, **kwargs)
        # Populate liturgy choices from Service model
        services = db.session.scalars(
            db.select(Service).order_by(Service.name)
        ).all()
        self.liturgy.choices = [(service.name, service.name) for service in services]

    def validate_last_name(self, field):
        """Validate that the primary key (last_name, first_name) doesn't already exist."""
        # Skip validation if both last_name and first_name haven't changed
        new_first_name = self.first_name.data or None
        if (self.original_last_name and 
            field.data == self.original_last_name and
            new_first_name == self.original_first_name):
            return

        # Check if primary key already exists
        existing = db.session.get(Prosphora, (field.data, new_first_name))
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
            db.session.add(prosphora)

        # Update fields
        prosphora.last_name = self.last_name.data
        prosphora.first_name = self.first_name.data
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
        prosphora.quantity = self.quantity.data or 1
        prosphora.paid_through = self.paid_through.data or None
        prosphora.liturgy = self.liturgy.data
        prosphora.notes = self.notes.data or None

        db.session.commit()
        return True

