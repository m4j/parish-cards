from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, SelectMultipleField, EmailField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional
from wtforms.widgets import ListWidget, CheckboxInput

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

    signature_date = StringField('Member Signature (date only)', validators=[DataRequired()])
    spouse_signature_date = StringField('Spouse Signature (date only)', validators=[Optional()])

    save = SubmitField('Save')
    register = SubmitField('Register')

    def loadApplication(self, app):
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

    def saveApplication(self, app):
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

