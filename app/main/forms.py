from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    search_term = StringField('Type word to search, like “irina”, or “Иван”. Word fragments work too, like “mar” or “joh”', render_kw={'autofocus': True})
    submit_search = SubmitField('Search')

