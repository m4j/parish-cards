from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, SelectMultipleField, EmailField, IntegerField, RadioField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import ListWidget, CheckboxInput
from types import SimpleNamespace
from werkzeug.datastructures import MultiDict
from ..validators import ISOYearMonthValidator, ISOYearMonthDayValidator

CHOICES1 = [ 'Altar Service', 'Brotherhood', 'Sisterhood']
CHOICES2 = [ 'Cemetery Care', 'Choir', 'Annual Bazaar']
CHOICES3 = [ 'Church Cleanup', 'Prosphora Baking', 'As Needed']

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ApplicationForm(FlaskForm):
    ru_name = StringField('Last, first name in Russian (including patronymic, if applicable)', validators=[DataRequired()], render_kw={'autofocus': True, 'placeholder': 'Смирнов Иван Петрович'})
    en_name = StringField('Last, first name in English', validators=[DataRequired()], render_kw={'placeholder': 'Smirnov Ivan'})
    saints_day = StringField('Saint’s Day', validators=[Optional()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female')])

    spouse_ru_name = StringField('Last, first name in Russian (including patronymic, if applicable)', render_kw={'placeholder': 'Смирнова Мария Ивановна'}, validators=[Optional()])
    spouse_en_name = StringField('Last, first name in English', render_kw={'placeholder': 'Smirnova Maria'}, validators=[Optional()])
    spouse_saints_day = StringField('Saint’s Day', validators=[Optional()])
    spouse_religion_denomination = StringField('Religion/Denomination', validators=[Optional()])

    street = StringField('Street', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    zip_code = StringField('Zip', validators=[DataRequired()])
    home_phone = StringField('Home Phone', validators=[Optional()])
    cell_phone = StringField('Cell Phone', validators=[Optional()])
    email = EmailField('E-mail', validators=[Optional()])
    spouse_cell_phone = StringField('Spouse’s Cell Phone', validators=[Optional()])
    spouse_email = EmailField('Spouse’s E-mail', validators=[Optional()])

    child1_name = StringField('Name', validators=[Optional()])
    child1_saints_day = StringField('Saint’s Day', validators=[Optional()])
    child1_age = IntegerField('Age', validators=[Optional()])

    child2_name = StringField('Name', validators=[Optional()])
    child2_saints_day = StringField('Saint’s Day', validators=[Optional()])
    child2_age = IntegerField('Age', validators=[Optional()])

    child3_name = StringField('Name', validators=[Optional()])
    child3_saints_day = StringField('Saint’s Day', validators=[Optional()])
    child3_age = IntegerField('Age', validators=[Optional()])

    child4_name = StringField('Name', validators=[Optional()])
    child4_saints_day = StringField('Saint’s Day', validators=[Optional()])
    child4_age = IntegerField('Age', validators=[Optional()])

    child5_name = StringField('Name', validators=[Optional()])
    child5_saints_day = StringField('Saint’s Day', validators=[Optional()])
    child5_age = IntegerField('Age', validators=[Optional()])

    interests1 = MultiCheckboxField('', choices=CHOICES1)
    interests2 = MultiCheckboxField('', choices=CHOICES2)
    interests3 = MultiCheckboxField('', choices=CHOICES3)

    signature_date = StringField('Member Signature (date only)', validators=[DataRequired(), ISOYearMonthDayValidator() ])
    spouse_signature_date = StringField('Spouse Signature (date only)', validators=[Optional(), ISOYearMonthDayValidator()])

    save = SubmitField('Save')
    register = SubmitField('Register')

    def load_application(self, app):
        self.ru_name.data = app.ru_name
        self.en_name.data = app.en_name
        self.saints_day.data = app.saints_day
        self.gender.data = app.gender

        self.spouse_ru_name.data = app.spouse_ru_name
        self.spouse_en_name.data = app.spouse_en_name
        self.spouse_saints_day.data = app.spouse_saints_day
        self.spouse_religion_denomination.data = app.spouse_religion_denomination

        self.street.data = app.street
        self.city.data = app.city
        self.state.data = app.state
        self.zip_code.data = app.zip_code
        self.home_phone.data = app.home_phone
        self.cell_phone.data = app.cell_phone
        self.email.data = app.email
        self.spouse_cell_phone.data = app.spouse_cell_phone
        self.spouse_email.data = app.spouse_email

        self.child1_name.data       = app.child1_name
        self.child1_saints_day.data = app.child1_saints_day
        self.child1_age.data        = app.child1_age

        self.child2_name.data       = app.child2_name
        self.child2_saints_day.data = app.child2_saints_day
        self.child2_age.data        = app.child2_age

        self.child3_name.data       = app.child3_name
        self.child3_saints_day.data = app.child3_saints_day
        self.child3_age.data        = app.child3_age

        self.child4_name.data       = app.child4_name
        self.child4_saints_day.data = app.child4_saints_day
        self.child4_age.data        = app.child4_age

        self.child5_name.data       = app.child5_name
        self.child5_saints_day.data = app.child5_saints_day
        self.child5_age.data        = app.child5_age

        self.signature_date.data = app.signature_date
        self.spouse_signature_date.data = app.spouse_signature_date

        interestsList = app.interests.split(',')
        self.interests1.data = list(filter(lambda each: each in CHOICES1, interestsList))
        self.interests2.data = list(filter(lambda each: each in CHOICES2, interestsList))
        self.interests3.data = list(filter(lambda each: each in CHOICES3, interestsList))

    def save_application(self, app):
        app.ru_name = self.ru_name.data
        app.en_name = self.en_name.data
        app.saints_day = self.saints_day.data
        app.gender = self.gender.data

        app.spouse_ru_name = self.spouse_ru_name.data
        app.spouse_en_name = self.spouse_en_name.data
        app.spouse_saints_day = self.spouse_saints_day.data
        app.spouse_religion_denomination = self.spouse_religion_denomination.data

        app.street = self.street.data
        app.city = self.city.data
        app.state = self.state.data
        app.zip_code = self.zip_code.data
        app.home_phone = self.home_phone.data
        app.cell_phone = self.cell_phone.data
        app.email = self.email.data
        app.spouse_cell_phone = self.spouse_cell_phone.data
        app.spouse_email = self.spouse_email.data

        app.child1_name =       self.child1_name.data
        app.child1_saints_day = self.child1_saints_day.data
        app.child1_age =        self.child1_age.data

        app.child2_name =       self.child2_name.data
        app.child2_saints_day = self.child2_saints_day.data
        app.child2_age =        self.child2_age.data

        app.child3_name =       self.child3_name.data
        app.child3_saints_day = self.child3_saints_day.data
        app.child3_age =        self.child3_age.data

        app.child4_name =       self.child4_name.data
        app.child4_saints_day = self.child4_saints_day.data
        app.child4_age =        self.child4_age.data

        app.child5_name =       self.child5_name.data
        app.child5_saints_day = self.child5_saints_day.data
        app.child5_age =        self.child5_age.data

        app.interests = ','.join(self.interests1.data + self.interests2.data + self.interests3.data)
        app.signature_date = self.signature_date.data
        app.spouse_signature_date = self.spouse_signature_date.data

class ApplicantSubForm(Form):
    names = StringField()
    ru_name_last = StringField('Last name in Russian', validators=[DataRequired()])
    ru_name_first = StringField('First name in Russian', validators=[DataRequired()])
    ru_name_patronymic = StringField('Patronymic name in Russian', validators=[Optional()])
    en_name_last = StringField('Last name in English', validators=[DataRequired()])
    en_name_first = StringField('First name in English', validators=[DataRequired()])
    dues_amount = IntegerField('Monthly dues', default=35, validators=[DataRequired()])
    do_register = RadioField(
            choices=[
                ('as_member', 'Register as new parish member'),
                ('as_non_member', 'Only store personal information')],
            default='as_member')

class ApplicantsRegistrationForm(FlaskForm):
    applicants = FieldList(FormField(ApplicantSubForm))
    as_of_date = StringField('As of date (YYYY-MM)', validators=[DataRequired(), ISOYearMonthValidator()])
    register = SubmitField('Register')

    @classmethod
    def make_with_form_data(cls, form_data):
        form = cls(MultiDict(form_data))
        return form

    def consider_loading_application(self, app):
        if len(self.applicants.data) == 0:
            self.load_application(app)

    def load_application(self, app):
        applicant_data = self._name_components(app.ru_name, app.en_name)
        self.applicants.append_entry(applicant_data)
        if app.spouse_en_name:
            applicant_data = self._name_components(app.spouse_ru_name, app.spouse_en_name)
            if not app.spouse_signature_date:
                applicant_data = applicant_data | { 'do_register': 'as_non_member' }
            self.applicants.append_entry(applicant_data)

    def applicant(self):
        data = self.applicants.data[0]
        return SimpleNamespace(**data)

    def spouse(self):
        if len(self.applicants.data) < 2:
            return None
        data = self.applicants.data[1]
        return SimpleNamespace(**data)

    def _name_components(self, ru_name, en_name):
        name_components = { 'names': f'{en_name} ({ru_name})' }
        name_components = name_components | self._name_components_ru(ru_name)
        name_components = name_components | self._name_components_en(en_name)
        return name_components

    def _name_components_ru(self, name):
        san = name.translate(name.maketrans(',;', '  '))
        names = [name for name in san.split(' ') if len(san) > 0]
        names = [x.strip() for x in names]
        names = [x for x in names if x]
        if len(names) == 3:
            return {
                    'ru_name_last': names[0],
                    'ru_name_first': names[1],
                    'ru_name_patronymic': names[2],
                    }
        if len(names) == 2:
            return {
                    'ru_name_last': names[0],
                    'ru_name_first': names[1],
                    }
        return {}

    def _name_components_en(self, name):
        san = name.translate(name.maketrans(',;', '  '))
        names = [name for name in san.split(' ') if len(san) > 0]
        names = [x.strip() for x in names]
        names = [x for x in names if x]
        if len(names) >= 2:
            last = names.pop(0)
            first = ' '.join(names)
            return {
                    'en_name_last': last,
                    'en_name_first': first,
                    }
        return {}

class UpdateDecisionSubForm(Form):
    update_decision = RadioField(
            choices=[
                ('update', 'Prefer <em>Application</em> (update <em>Our Records</em>)'),
                ('use_as_is', 'Prefer <em>Our Records</em> (disregard <em>Application</em>)')
            ],
            validators=[DataRequired()]
        )

class UpdateDecisionsForm(FlaskForm):
    decisions = FieldList(FormField(UpdateDecisionSubForm))
    register = SubmitField('Continue')

    def append_decision(self):
        self.decisions.append_entry()
