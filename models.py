"""
Imported into main app file. This file contains all classes for the
models used in the journal database.
"""

import datetime

from flask import flash
from flask_bcrypt import generate_password_hash
from flask_login import UserMixin
from peewee import *


DATABASE = SqliteDatabase('journal.db')


class User(UserMixin, Model):
    """ Model for creating user in database. """
    username = CharField(max_length=16, unique=True)
    password = CharField(max_length=100, unique=True)

    class Meta:
        database = DATABASE

    @classmethod
    def create_user(cls, username, password):
        try:
            cls.create(
                username=username,
                password=generate_password_hash(password)
            )
        except IntegrityError:
            raise ValueError('User Exists')

    def get_tag_journal(self, tag):
        return Entry.select().where(
            (Entry.user == self) & Entry.tags.contains(tag))

    def user_journal(self):
        return Entry.select().where(
            Entry.user == self).order_by(Entry.date.desc())

    def most_recent(self):
        return Entry.get(Entry.user == self)


class Entry(Model):
    user = ForeignKeyField(model=User, related_name='entries')
    tags = CharField(max_length=200)
    title = CharField(max_length=40, unique=True)
    date = DateTimeField(default=datetime.datetime.now().strftime('%Y-%m-%d'))
    date_created = DateTimeField(default=datetime.datetime.now())
    time_spent = DecimalField()
    learned = TextField()
    resources = TextField()

    class Meta:
        database = DATABASE
        order_by = ('-date_created',)

    @classmethod
    def create_entry(cls, user, tags, title, date,
                     time_spent, learned, resources):
        try:
            if '-' in title:
                raise ValueError()
            else:
                cls.create(
                    user=user,
                    tags=tags,
                    title=title,
                    date=date,
                    time_spent=time_spent,
                    learned=learned,
                    resources=resources
                )
                flash('Entry - [ ' + (title) + ' ] Created')
        except IntegrityError:
            flash('Entry with Title Already Exists', "errors")


def initialize():
    DATABASE.connect()
    DATABASE.create_tables([User, Entry], safe=True)
    DATABASE.close()
