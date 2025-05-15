from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional
from ..models import RecordSheet, db
from sqlalchemy import func

class RecordSheetForm(FlaskForm):
    identifier = StringField('Identifier', validators=[DataRequired()])
    date = StringField('Date', validators=[DataRequired()])
    description = SelectField('Description', validators=[Optional()], coerce=str,
                            render_kw={
                                'class': 'form-control',
                                'data-editable': 'true',
                                'data-placeholder': 'Select or type a description'
                            })
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super(RecordSheetForm, self).__init__(*args, **kwargs)
        # Get all unique descriptions from the record_sheet table
        descriptions = db.session.scalars(
            db.select(RecordSheet.description)
            .filter(RecordSheet.description.isnot(None))
            .filter(RecordSheet.identifier.isnot('9999-12-31'))
            .distinct()
            .order_by(RecordSheet.description)
        ).all()
        # Add an empty choice for optional selection
        self.description.choices = [('', '')] + [(d, d) for d in descriptions if d]

    @classmethod
    def load(cls, record_id):
        """Load a record sheet into the form."""
        record_sheet = db.session.get(RecordSheet, record_id)
        if not record_sheet:
            return None
        return cls(obj=record_sheet)

    def save(self, record_id):
        """Save form data to the record sheet."""
        record_sheet = db.session.get(RecordSheet, record_id)
        if not record_sheet:
            return False
            
        self.populate_obj(record_sheet)
        db.session.commit()
        return True 