from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Card(db.Model):
    __tablename__ = 'cards'
    member_last           = db.Column(db.String, primary_key=True)
    member_first          = db.Column(db.String, primary_key=True)
    member_first_other    = db.Column(db.String)
    member_middle         = db.Column(db.String)
    member_maiden         = db.Column(db.String)
    ru_member_last        = db.Column(db.String)
    ru_member_maiden      = db.Column(db.String)
    ru_member_first       = db.Column(db.String)
    ru_member_first_other = db.Column(db.String)
    ru_member_patronymic  = db.Column(db.String)
    member_from           = db.Column(db.String)
    dues_amount           = db.Column(db.Numeric, default=35)
    dues_paid_through     = db.Column(db.String)
    family_duid           = db.Column(db.String)
    notes                 = db.Column(db.String)
    guid                  = db.Column(db.String, unique=True)
    application_guid      = db.Column(db.Uuid(native_uuid=False), db.ForeignKey('applications.guid'))
    application           = db.relationship('Application', back_populates='cards')

class Application(db.Model):
    __tablename__ = 'applications'
    guid                  = db.Column(db.Uuid(native_uuid=False), primary_key=True)
    ru_name               = db.Column(db.String, nullable=False)
    en_name               = db.Column(db.String, nullable=False)
    saints_day            = db.Column(db.String)
    gender                = db.Column(db.String(1))
    
    spouse_ru_name        = db.Column(db.String)
    spouse_en_name        = db.Column(db.String)
    spouse_saints_day     = db.Column(db.String)
    spouse_religion_denomination = db.Column(db.String)

    street                = db.Column(db.String, nullable=False)
    city                  = db.Column(db.String, nullable=False)
    state                 = db.Column(db.String, nullable=False)
    zip_code              = db.Column(db.String, nullable=False)
    home_phone            = db.Column(db.String)
    cell_phone            = db.Column(db.String)
    email                 = db.Column(db.String)
    spouse_cell_phone     = db.Column(db.String)
    spouse_email          = db.Column(db.String)

    child1_name           = db.Column(db.String)
    child1_saints_day     = db.Column(db.String)
    child1_age            = db.Column(db.Integer)

    child2_name           = db.Column(db.String)
    child2_saints_day     = db.Column(db.String)
    child2_age            = db.Column(db.Integer)

    child3_name           = db.Column(db.String)
    child3_saints_day     = db.Column(db.String)
    child3_age            = db.Column(db.Integer)

    child4_name           = db.Column(db.String)
    child4_saints_day     = db.Column(db.String)
    child4_age            = db.Column(db.Integer)

    child5_name           = db.Column(db.String)
    child5_saints_day     = db.Column(db.String)
    child5_age            = db.Column(db.Integer)

    interests             = db.Column(db.String)

    signature_date        = db.Column(db.String, nullable=False)
    spouse_signature_date = db.Column(db.String)
    cards                 = db.relationship('Card', back_populates="application")

    def __format_names(self, name, glue, spouse_name):
        if spouse_name:
            return f'{name} {glue} {spouse_name}'
        return name

    def format_en_names(self):
        return self.__format_names(self.en_name, 'and', self.spouse_en_name)

    def format_ru_names(self):
        return self.__format_names(self.ru_name, 'и', self.spouse_ru_name)



