from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

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

