from sqlalchemy.ext.hybrid import Comparator, hybrid_property
from sqlalchemy import func
from . import db

import uuid

class IdentityMixin:
    guid = db.Column(db.Uuid(native_uuid=False), unique=True, default=uuid.uuid4)

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
    payments            = db.relationship('PaymentSubProsphora', back_populates='membership')
    person              = db.relationship('Person', back_populates='prosphora')

    __table_args__ = (
        db.PrimaryKeyConstraint('last_name', 'first_name'),
        db.ForeignKeyConstraint(
            ['p_last_name', 'p_first_name'], ['person.last', 'person.first']
        )
    )

    def __repr__(self):
        if self.first_name:
            return f'{self.last_name}, {self.first_name}'
        return self.last_name

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
    payments              = db.relationship('PaymentSubDues', back_populates='membership')

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
    validation_message = db.Column(db.String)

class PaymentCommonMixin:
    payor         = db.Column(db.String)
    date          = db.Column(db.String)

    @db.declared_attr
    def method(cls):
        return db.Column(db.String, db.ForeignKey('payment_method.method'))
    
    identifier    = db.Column(db.String, nullable=True)
    amount        = db.Column(db.Integer)
    comment       = db.Column(db.String)

    @db.declared_attr
    def payment_method(self):
        return db.relationship(PaymentMethod, uselist=False, viewonly=True)

class Payment(IdentityMixin, PaymentCommonMixin, db.Model):
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

    dues      = db.relationship('PaymentSubDues', back_populates='payment', cascade="all, delete-orphan")
    prosphora = db.relationship('PaymentSubProsphora', back_populates='payment', cascade="all, delete-orphan")
    misc      = db.relationship('PaymentSubMisc', back_populates='payment', cascade="all, delete-orphan")

class PaymentSubMixin(IdentityMixin, PaymentCommonMixin):
    @db.declared_attr.directive
    def __table_args__(cls):
        return (
            db.PrimaryKeyConstraint('guid'),
            db.ForeignKeyConstraint(
                ['payor', 'date', 'method', 'identifier'],
                ['payment.payor', 'payment.date', 'payment.method', 'payment.identifier']
            ),
        )

class NameAndRangeMixin:
    last_name     = db.Column(db.String)
    first_name    = db.Column(db.String)
    paid_from     = db.Column(db.String, db.ForeignKey('yyyy_mm.year_month'))
    paid_through  = db.Column(db.String, db.ForeignKey('yyyy_mm.year_month'))
    
    paid_from_year_month = db.relationship(
        'YearMonth',
        foreign_keys=[paid_from],
        primaryjoin=lambda: NameAndRangeMixin.paid_from == YearMonth.year_month,
        uselist=False,
        viewonly=True
    )
    
    paid_through_year_month = db.relationship(
        'YearMonth',
        foreign_keys=[paid_through],
        primaryjoin=lambda: NameAndRangeMixin.paid_through == YearMonth.year_month,
        uselist=False,
        viewonly=True
    )

    def format_date_range(self):
        """Format the date range using English month and year from YearMonth records."""
        if not self.paid_from_year_month or not self.paid_through_year_month:
            return f"{self.paid_from} - {self.paid_through}"
            
        if self.paid_from_year_month.en_yy == self.paid_through_year_month.en_yy:
            # Same year, use just month for start date
            return f"{self.paid_from_year_month.en_mon}–{self.paid_through_year_month.en_mon_yy}"
        else:
            # Different years, show full month-year for both
            return f"{self.paid_from_year_month.en_mon_yy}–{self.paid_through_year_month.en_mon_yy}"

    def description(self):
        """Return a formatted description of the payment range."""
        return f"{self.last_name}, {self.first_name} ({self.format_date_range()})"

class PaymentSubDues(PaymentSubMixin, NameAndRangeMixin, db.Model):
    __tablename__ = 'payment_sub_dues'

    @db.declared_attr.directive
    def __table_args__(cls):
        return PaymentSubMixin.__table_args__ + (
            db.ForeignKeyConstraint(
                ['last_name', 'first_name'],
                ['card.last_name', 'card.first_name']
            ),
        )

    payment = db.relationship(Payment, back_populates='dues')
    membership = db.relationship(
        Card,
        back_populates='payments',
        order_by=[NameAndRangeMixin.paid_from, NameAndRangeMixin.paid_through]
    )

    def __repr__(self):
        return f'{self.date} {self.payor} {self.method} {self.identifier} {self.amount} {self.paid_from}--{self.paid_through}'

class PaymentSubProsphora(PaymentSubMixin, NameAndRangeMixin, db.Model):
    __tablename__      = 'payment_sub_prosphora'
    quantity           = db.Column(db.Integer)
    with_twelve_feasts = db.Column(db.Boolean, default=False, nullable=False)

    @db.declared_attr.directive
    def __table_args__(cls):
        return PaymentSubMixin.__table_args__ + (
            db.ForeignKeyConstraint(
                ['last_name', 'first_name'],
                ['prosphora.last_name', 'prosphora.first_name'],
            ),
        )

    payment   = db.relationship(Payment, back_populates='prosphora')
    membership = db.relationship(
        Prosphora,
        back_populates='payments',
        order_by=[NameAndRangeMixin.paid_from, NameAndRangeMixin.paid_through]
    )

    def description(self):
        """Return a formatted description of the prosphora payment range."""
        quantity_str = f"({self.quantity})" 
        feasts_str = " +12 Feasts" if self.with_twelve_feasts else ""
        return f"Prosphora{quantity_str}{feasts_str}: {super().description()}"

class PaymentSubMisc(PaymentSubMixin, db.Model):
    __tablename__ = 'payment_sub_misc'
    
    # Additional fields specific to misc payments
    category = db.Column(db.String, db.ForeignKey('payment_sub_misc_category.category', onupdate='CASCADE'), nullable=False)

    # Define relationships
    payment = db.relationship(Payment, back_populates='misc')
    category_info = db.relationship('PaymentSubMiscCategory', backref='payments')

    @db.declared_attr.directive
    def __table_args__(cls):
        return PaymentSubMixin.__table_args__

    def description(self):
        """Return a formatted description of the miscellaneous payment."""
        comment_str = f" ({self.comment})" if self.comment else ""
        return f"{self.category}{comment_str}"

    def __repr__(self):
        return f'{self.date} {self.payor} {self.method} {self.identifier} {self.amount} {self.category}'

# Category model
class PaymentSubMiscCategory(db.Model):
    __tablename__ = 'payment_sub_misc_category'
    
    category = db.Column(db.String, primary_key=True)
    ru_category = db.Column(db.String, unique=True)

class YearMonth(db.Model):
    """Model for the yyyy_mm table that stores month-year information in various formats"""
    __tablename__ = 'yyyy_mm'
    
    year_month = db.Column(db.String(7), primary_key=True, nullable=False)
    en_month_year = db.Column(db.String)
    ru_month_year = db.Column(db.String)
    en_mon_yy = db.Column(db.String)
    en_yy = db.Column(db.String)
    en_mon = db.Column(db.String)

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

def find_sub_dues_payments(fragment):
    return _find_sub_payments(fragment, PaymentSubDues)

def find_sub_prosphora_payments(fragment):
    return _find_sub_payments(fragment, PaymentSubProsphora)

def _find_sub_payments(fragment, model):
    search_term = f'%{fragment}%'
    return db.session.scalars(
        db.select(model).filter(
            db.or_(
                model.payor.ilike(search_term),
                model.date.ilike(search_term),
                model.method.ilike(search_term),
                model.identifier.ilike(search_term),
                model.amount.ilike(search_term),
                model.last_name.ilike(search_term),
                model.first_name.ilike(search_term),
                model.paid_from.ilike(search_term),
                model.paid_through.ilike(search_term),
                model.comment.ilike(search_term)
            ))
        .order_by(
            model.paid_from.desc(),
            model.paid_through.desc(),
        )).all()

def dues_range_containing_date(date, first_name, last_name):
    return _range_containing_date(PaymentSubDues, date, first_name, last_name)

def prosphora_range_containing_date(date, first_name, last_name):
    return _range_containing_date(PaymentSubProsphora, date, first_name, last_name)

def _range_containing_date(model, date, first_name, last_name):
    return db.session.execute(
        db.select(model).filter(
            db.and_(
                model.last_name == last_name,
                model.first_name == first_name,
                model.paid_from <= date,
                date <= model.paid_through,
            ))).scalar()

def find_payments_with_multiple_subs(fragment=None):
    search_conditions = []
    if fragment:
        search_term = f'%{fragment}%'
        search_conditions = [
            db.or_(
                PaymentSubDues.payor.ilike(search_term),
                PaymentSubDues.date.ilike(search_term),
                PaymentSubDues.method.ilike(search_term),
                PaymentSubDues.identifier.ilike(search_term),
                PaymentSubDues.amount.cast(db.String).ilike(search_term),
                PaymentSubDues.comment.ilike(search_term),
                PaymentSubDues.last_name.ilike(search_term),
                PaymentSubDues.first_name.ilike(search_term),
                PaymentSubDues.paid_from.ilike(search_term),
                PaymentSubDues.paid_through.ilike(search_term)
            )
        ]

    dues_subq = (
        db.select(Payment.payor, Payment.date, Payment.method, Payment.identifier)
        .join(PaymentSubDues)
        .filter(*search_conditions)
    ).subquery()
    
    if fragment:
        search_conditions = [
            db.or_(
                PaymentSubProsphora.payor.ilike(search_term),
                PaymentSubProsphora.date.ilike(search_term),
                PaymentSubProsphora.method.ilike(search_term),
                PaymentSubProsphora.identifier.ilike(search_term),
                PaymentSubProsphora.amount.cast(db.String).ilike(search_term),
                PaymentSubProsphora.comment.ilike(search_term),
                PaymentSubProsphora.last_name.ilike(search_term),
                PaymentSubProsphora.first_name.ilike(search_term),
                PaymentSubProsphora.paid_from.ilike(search_term),
                PaymentSubProsphora.paid_through.ilike(search_term)
            )
        ]

    prosphora_subq = (
        db.select(Payment.payor, Payment.date, Payment.method, Payment.identifier)
        .join(PaymentSubProsphora)
        .filter(*search_conditions)
    ).subquery()
    
    if fragment:
        search_conditions = [
            db.or_(
                PaymentSubMisc.payor.ilike(search_term),
                PaymentSubMisc.date.ilike(search_term),
                PaymentSubMisc.method.ilike(search_term),
                PaymentSubMisc.identifier.ilike(search_term),
                PaymentSubMisc.amount.cast(db.String).ilike(search_term),
                PaymentSubMisc.comment.ilike(search_term),
                PaymentSubMisc.category.ilike(search_term)
            )
        ]

    misc_subq = (
        db.select(Payment.payor, Payment.date, Payment.method, Payment.identifier)
        .join(PaymentSubMisc)
        .filter(*search_conditions)
    ).subquery()

    # Union all subqueries
    union_subq = (
        db.union_all(
            dues_subq.select(),
            prosphora_subq.select(),
            misc_subq.select()
        )
    ).subquery()

    # Count occurrences and filter for more than one
    query = (
        db.select(
            Payment,
            db.func.count().label('sub_count')
        )
        .join(
            union_subq,
            db.and_(
                Payment.payor == union_subq.c.payor,
                Payment.date == union_subq.c.date,
                Payment.method == union_subq.c.method,
                db.or_(
                    db.and_(Payment.identifier == union_subq.c.identifier),
                    db.and_(Payment.identifier.is_(None), union_subq.c.identifier.is_(None))
                )
            )
        )
        .group_by(Payment)
        .having(db.func.count() > 1)
        .order_by(Payment.date.desc())
    )

    return db.session.execute(query).all()

# results = find_payments_with_multiple_subs()
# for payment, count in results:
    # print(f"Payment {payment.payor} on {payment.date} has {count} sub-payments")

