from flask_wtf import FlaskForm
from wtforms import Form, StringField, SubmitField, SelectMultipleField, EmailField, IntegerField
from wtforms.validators import DataRequired
from wtforms.widgets import ListWidget, CheckboxInput

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

class ChildForm(Form):
    name = StringField('Name')
    saints_day = StringField('Saint’s Day')
    age = IntegerField('Age')

class NewMemberForm(FlaskForm):
    ru_name = StringField('Name in Russian (including patronymic, if applicable)', validators=[DataRequired()], render_kw={'autofocus': True})
    en_name = StringField('Name in English', validators=[DataRequired()])
    saints_day = StringField('Saint’s Day')
    
    spouse_ru_name = StringField('Name in Russian (including patronymic, if applicable)')
    spouse_en_name = StringField('Name in English')
    spouse_saints_day = StringField('Saint’s Day')
    spouse_religion_denomination = StringField('Religion/Denomination')

    street = StringField('Street', validators=[DataRequired()])
    city = StringField('City', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    zip_code = StringField('Zip', validators=[DataRequired()])
    home_phone = StringField('Home Phone')
    cell_phone = StringField('Cell Phone')
    email = EmailField('E-mail')
    spouse_cell_phone = StringField('Spouse’s Cell Phone')
    spouse_email = EmailField('Spouse’s E-mail')

    child1 = ChildForm()
    child2 = ChildForm()
    child3 = ChildForm()
    child4 = ChildForm()
    child5 = ChildForm()

    interests1 = MultiCheckboxField('',
            choices=[ 'Altar Service', 'Brotherhood', 'Sisterhood'])

    interests2 = MultiCheckboxField('',
            choices=[ 'Cemetery Care', 'Choir', 'Annual Bazaar'])

    interests3 = MultiCheckboxField('',
            choices=[ 'Church Cleanup', 'Prosphora Baking', 'As Needed'])

    submit = SubmitField('Submit')

def process(form):
    breakpoint()
    return ('30966795-4d78-40f7-86b0-eea3d74fbf95', None)
