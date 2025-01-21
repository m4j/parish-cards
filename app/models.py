from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy import func
from . import db

import uuid

class IdentityMixin:
    guid = db.Column(db.Uuid(native_uuid=False), unique=True)

class CaseInsensitiveComparator(Comparator):
    def __eq__(self, other):
        return func.lower(self.__clause_element__()) == func.lower(other)

class Prosphora(IdentityMixin, db.Model):
    __tablename__ = 'prosphora'
    last_name           = db.Column(db.String)
    first_name          = db.Column(db.String)
    family_name         = db.Column(db.String)
    ru_last_name        = db.Column(db.String)
    ru_first_name       = db.Column(db.String)
    ru_family_name      = db.Column(db.String)
    p_last_name         = db.Column(db.String)
    p_first_name        = db.Column(db.String)
    quantity            = db.Column(db.Integer, default=1)
    paid_through        = db.Column(db.String)
    liturgy             = db.Column(db.String)
    notes               = db.Column(db.String)
    payments            = db.relationship('PaymentSubProsphora', back_populates='prosphora')
    person              = db.relationship('Person', back_populates='prosphora')

    __table_args__ = (
        db.PrimaryKeyConstraint('last_name', 'first_name'),
        db.ForeignKeyConstraint(
            ['p_last_name', 'p_first_name'], ['person.last', 'person.first']
        )
    )

class Card(IdentityMixin, db.Model):
    __tablename__ = 'card'
    last_name           = db.Column(db.String)
    first_name          = db.Column(db.String)
    other_name          = db.Column(db.String)
    middle_name         = db.Column(db.String)
    maiden_name         = db.Column(db.String)
    ru_last_name        = db.Column(db.String)
    ru_maiden_name      = db.Column(db.String)
    ru_first_name       = db.Column(db.String)
    ru_other_name       = db.Column(db.String)
    ru_patronymic_name  = db.Column(db.String)
    membership_from       = db.Column(db.String)
    membership_through    = db.Column(db.String)
    membership_termination_reason = db.Column(db.String)
    dues_amount           = db.Column(db.Integer)
    dues_paid_through     = db.Column(db.String)
    notes                 = db.Column(db.String)
    application_guid      = db.Column(db.Uuid(native_uuid=False), db.ForeignKey('application.guid'))
    application           = db.relationship('Application', back_populates='card')
    person                = db.relationship('Person', back_populates='card')
    payments              = db.relationship('PaymentSubDues', back_populates='card')

    @hybrid_property
    def i_last_name(self):
        return self.last_name.lower()

    @i_last_name.inplace.comparator
    @classmethod
    def _i_last_name_comparator(cls) -> CaseInsensitiveComparator:
        return CaseInsensitiveComparator(cls.last_name)

    @hybrid_property
    def i_first_name(self):
        return self.first_name.lower()

    @i_first_name.inplace.comparator
    @classmethod
    def _i_first_name_comparator(cls) -> CaseInsensitiveComparator:
        return CaseInsensitiveComparator(cls.first_name)

    def __init__(self, app, person, applicant, as_of_date):
        self.guid = str(uuid.uuid4())
        self.application = app
        self.person = person
        self.ru_last_name = applicant.ru_name_last
        self.ru_first_name = applicant.ru_name_first
        self.ru_patronymic_name = applicant.ru_name_patronymic
        self.membership_from = as_of_date
        self.dues_amount = applicant.dues_amount

    __table_args__ = (
        db.PrimaryKeyConstraint('last_name', 'first_name'),
        db.ForeignKeyConstraint(
            ['last_name', 'first_name'], ['person.last', 'person.first']
        )
    )

    def __repr__(self):
        fullname = f'{self.last_name}, {self.first_name}{" †" if self.membership_termination_reason == "Deceased" else ""}'
        return fullname

def get_postal_code(zip_code):
    return zip_code.split('-')[0].strip()

def get_plus4(zip_code):
    split = zip_code.split('-')
    return split[1].strip() if len(split) > 1 else None

class Person(IdentityMixin, db.Model):
    __tablename__ = 'person'
    last    = db.Column(db.String)
    first   = db.Column(db.String)
    email   = db.Column(db.String)
    home_phone     = db.Column(db.String)
    mobile_phone   = db.Column(db.String)
    work_phone     = db.Column(db.String)
    gender         = db.Column(db.String)
    address        = db.Column(db.String)
    city           = db.Column(db.String)
    state_region   = db.Column(db.String)
    postal_code    = db.Column(db.String)
    plus_4         = db.Column(db.String)
    date_of_birth  = db.Column(db.String)
    date_of_death  = db.Column(db.String)
    note           = db.Column(db.String)
    card           = db.relationship('Card', uselist=False, back_populates='person')
    prosphora      = db.relationship('Prosphora', uselist=False, back_populates='person')
    marriage       = db.relationship(
        'Marriage',
        uselist=False,
        primaryjoin = 'and_(Marriage.status == "Active", or_(and_(foreign(Person.last) == Marriage.husband_last, foreign(Person.first) == Marriage.husband_first), and_(foreign(Person.last) == Marriage.wife_last, foreign(Person.first) == Marriage.wife_first)))'
    )

    __table_args__ = (
        db.PrimaryKeyConstraint('last', 'first'),
    )

    def __init__(self, app, applicant):
        self.guid = str(uuid.uuid4())
        self.last = applicant.en_name_last
        self.first = applicant.en_name_first
        self.email = app.email
        self.home_phone = app.home_phone
        self.mobile_phone = app.cell_phone
        self.gender = app.gender
        self.address = app.street
        self.city = app.city
        self.state_region = app.state
        self.postal_code = get_postal_code(app.zip_code)
        self.plus_4 = get_plus4(app.zip_code)

    @hybrid_property
    def i_last(self):
        return self.last.lower()

    @i_last.inplace.comparator
    @classmethod
    def _i_last_comparator(cls):
        return CaseInsensitiveComparator(cls.last)

    @hybrid_property
    def i_first(self):
        return self.first.lower()

    @i_first.inplace.comparator
    @classmethod
    def _i_first_comparator(cls):
        return CaseInsensitiveComparator(cls.first)

    def update_from(self, other):
        self.last         = other.last
        self.first        = other.first
        self.email        = other.email
        self.home_phone   = other.home_phone
        self.mobile_phone = other.mobile_phone
        self.gender       = other.gender
        self.address      = other.address
        self.city         = other.city
        self.state_region = other.state_region
        self.postal_code  = other.postal_code
        self.plus_4       = other.plus_4

    @classmethod
    def make_spouse(cls, app, applicant):
        spouse = cls(app, applicant)
        spouse.email = app.spouse_email
        spouse.mobile_phone = app.spouse_cell_phone
        spouse.gender = 'F' if app.gender == 'M' else 'M'
        return spouse

    def full_name(self):
        return f'{self.last}, {self.first}'

    def full_name_address(self):
        return f'{self.full_name()} ({self.address}, {self.city} {self.state_region} {self.postal_code})'

    @property
    def spouse(self):
        m = self.marriage
        if m is None:
            return None
        return m.wife if m.husband == self else m.husband

class Marriage(db.Model):
    __tablename__ = 'marriage'
    husband_last   = db.Column(db.String)
    husband_first  = db.Column(db.String)
    wife_last      = db.Column(db.String)
    wife_first     = db.Column(db.String)
    status         = db.Column(db.String)

    @hybrid_property
    def i_husband_first(self):
        return self.husband_first.lower()

    @i_husband_first.inplace.comparator
    @classmethod
    def _i_husband_first_comparator(cls):
        return CaseInsensitiveComparator(cls.husband_first)

    @hybrid_property
    def i_husband_last(self):
        return self.husband_last.lower()

    @i_husband_last.inplace.comparator
    @classmethod
    def _i_husband_last_comparator(cls):
        return CaseInsensitiveComparator(cls.husband_last)

    @hybrid_property
    def i_wife_first(self):
        return self.wife_first.lower()

    @i_wife_first.inplace.comparator
    @classmethod
    def _i_wife_first_comparator(cls):
        return CaseInsensitiveComparator(cls.wife_first)

    @hybrid_property
    def i_wife_last(self):
        return self.wife_last.lower()

    @i_wife_last.inplace.comparator
    @classmethod
    def _i_wife_last_comparator(cls):
        return CaseInsensitiveComparator(cls.wife_last)

    def __init__(self, husband, wife, status='Active'):
        self.husband = husband
        self.wife = wife
        self.status = status

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'husband_last',
            'husband_first',
            'wife_last',
            'wife_first'
        ),
        db.ForeignKeyConstraint(
            ['husband_last', 'husband_first'], ['person.last', 'person.first']
        ),
        db.ForeignKeyConstraint(
            ['wife_last', 'wife_first'], ['person.last', 'person.first']
        ),
    )

    husband = db.relationship(
        'Person',
        foreign_keys = [husband_last, husband_first]
    )
    wife = db.relationship(
        'Person',
        foreign_keys = [wife_last, wife_first]
    )

class Application(IdentityMixin, db.Model):
    __tablename__ = 'application'
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
    card                  = db.relationship('Card', back_populates='application')

    __table_args__ = (
        db.PrimaryKeyConstraint('guid'),
    )

    def _format_names(self, name, glue, spouse_name):
        if spouse_name:
            return f'{name} {glue} {spouse_name}'
        return name

    def format_en_names(self):
        return self._format_names(self.en_name, 'and', self.spouse_en_name)

    def format_ru_names(self):
        return self._format_names(self.ru_name, 'и', self.spouse_ru_name)

    def is_registered(self):
        return len(self.card) > 0

class PaymentMethod(db.Model):
    __tablename__ = 'payment_method'
    method        = db.Column(db.String, primary_key=True)
    section       = db.Column(db.Integer)
    section_name  = db.Column(db.String)
    display_short = db.Column(db.String)
    display_full  = db.Column(db.String)
    display_long  = db.Column(db.String)

class PaymentCommonMixin:
    payor         = db.Column(db.String)
    date          = db.Column(db.String)
    method        = db.Column(db.String, db.ForeignKey('payment_method.method'))
    identifier    = db.Column(db.String, nullable=True)
    amount        = db.Column(db.Integer)
    comment       = db.Column(db.String)

    @db.declared_attr
    def payment_method(self):
        return db.relationship(PaymentMethod, uselist=False, viewonly=True)

class Payment(PaymentCommonMixin, db.Model):
    __tablename__ = 'payment'
    record_id     = db.Column(db.String, default='9999-12-31')

    __table_args__ = (
        db.PrimaryKeyConstraint(
            'payor',
            'date',
            'method',
            'identifier'
        ),
    )

    dues      = db.relationship('PaymentSubDues', back_populates='payment')
    prosphora = db.relationship('PaymentSubProsphora', back_populates='payment')

class PaymentSubDues(IdentityMixin, PaymentCommonMixin, db.Model):
    __tablename__ = 'payment_sub_dues'
    last_name     = db.Column(db.String)
    first_name    = db.Column(db.String)
    paid_from     = db.Column(db.String)
    paid_through  = db.Column(db.String)

    __table_args__ = (
        db.PrimaryKeyConstraint('guid'),
        db.ForeignKeyConstraint(
            ['payor', 'date', 'method', 'identifier'],
            ['payment.payor', 'payment.date', 'payment.method', 'payment.identifier']
        ),
        db.ForeignKeyConstraint(
            ['last_name', 'first_name'],
            ['card.last_name', 'card.first_name'],
        ),
    )

    payment = db.relationship(Payment, back_populates='dues')
    card    = db.relationship(
        Card,
        back_populates='payments',
        order_by=[paid_from, paid_through]
    )

    def __repr__(self):
        return f'{self.date} {self.payor} {self.method} {self.identifier} {self.amount} {self.paid_from}--{self.paid_through}'

class PaymentSubProsphora(IdentityMixin, PaymentCommonMixin, db.Model):
    __tablename__ = 'payment_sub_prosphora'
    last_name     = db.Column(db.String)
    first_name    = db.Column(db.String)
    paid_from     = db.Column(db.String)
    paid_through  = db.Column(db.String)
    quantity      = db.Column(db.Integer)
    with_twelve_feasts = db.Column(db.String(1), default='N')

    __table_args__ = (
        db.PrimaryKeyConstraint('guid'),
        db.ForeignKeyConstraint(
            ['payor', 'date', 'method', 'identifier'],
            ['payment.payor', 'payment.date', 'payment.method', 'payment.identifier']
        ),
        db.ForeignKeyConstraint(
            ['last_name', 'first_name'],
            ['prosphora.last_name', 'prosphora.first_name'],
        ),
    )

    payment   = db.relationship(Payment, back_populates='prosphora')
    prosphora = db.relationship(
        Prosphora,
        back_populates='payments',
        order_by=[paid_from, paid_through]
    )

def find_member(first_name, last_name):
    return db.session.execute(
            db.select(Card).filter(
                Card.i_first_name==first_name, Card.i_last_name==last_name
                )).scalar()

def find_person(first_name, last_name):
    return db.session.execute(
            db.select(Person).filter(
                Person.i_first==first_name, Person.i_last==last_name
                )).scalar()

def find_marriage(first_name, last_name):
    return db.session.execute(
            db.select(Marriage).filter(
                db.or_(
                    db.and_(Marriage.i_husband_first == first_name, Marriage.i_husband_last == last_name),
                    db.and_(Marriage.i_wife_first == first_name, Marriage.i_wife_last == last_name)
                    ))).scalar()

def find_active_marriage(h_first, h_last, w_first, w_last):
    return db.session.execute(
            db.select(Marriage).filter(
                db.and_(
                    Marriage.i_husband_first == h_first,
                    Marriage.i_husband_last == h_last,
                    Marriage.i_wife_first == w_first,
                    Marriage.i_wife_last == w_last,
                    Marriage.status == 'Active'
                    ))).scalar()

def find_active_marriage_of_husband(first_name, last_name):
    return db.session.execute(
            db.select(Marriage).filter(
                db.and_(
                    Marriage.i_husband_first == first_name,
                    Marriage.i_husband_last == last_name,
                    Marriage.status == 'Active'
                    ))).scalar()

def find_active_marriage_of_wife(first_name, last_name):
    return db.session.execute(
            db.select(Marriage).filter(
                db.and_(
                    Marriage.i_wife_first == first_name,
                    Marriage.i_wife_last == last_name,
                    Marriage.status == 'Active'
                    ))).scalar()

def find_all_payments(fragment):
    return find_sub_dues_payments(fragment)

def find_sub_dues_payments(fragment):
    search_term = f'%{fragment}%'
    return db.session.scalars(
        db.select(PaymentSubDues).filter(
            db.or_(
                PaymentSubDues.payor.ilike(search_term),
                PaymentSubDues.date.ilike(search_term),
                PaymentSubDues.method.ilike(search_term),
                PaymentSubDues.identifier.ilike(search_term),
                PaymentSubDues.amount.ilike(search_term),
                PaymentSubDues.last_name.ilike(search_term),
                PaymentSubDues.first_name.ilike(search_term),
                PaymentSubDues.paid_from.ilike(search_term),
                PaymentSubDues.paid_through.ilike(search_term),
                PaymentSubDues.comment.ilike(search_term)
            ))
        .order_by(
            PaymentSubDues.paid_from.desc(),
            PaymentSubDues.paid_through.desc(),
        )).all()

def date_within_other_dues_range(date, first, last):
    return db.session.scalars(
        db.select(PaymentSubDues).filter(
            db.and_(
                PaymentSubDues.last_name == last,
                PaymentSubDues.first_name == first,
                PaymentSubDues.paid_from <= date,
                date <= PaymentSubDues.paid_through,
            ))).first()

