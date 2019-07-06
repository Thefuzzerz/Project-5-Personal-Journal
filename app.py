"""
Learning Journal for Treehouse Python Course
A local web interface developed with Flask for users to create Journals.
Journals contain a user, tags, title, date, date created, what the user
learned and resources they should remember. While the project did not
require a registration page one was included for good practice. A default
user is created to skip this non-requirement.

Reviewed additional information on the Slugify library, Jinja, and
template filters.
"""
import datetime
import re

from flask import (Flask, g, render_template, flash, redirect,
                   url_for, request, abort)
from flask_bcrypt import check_password_hash
from flask_login import (LoginManager, login_user, logout_user,
                         current_user, login_required)
from unidecode import unidecode

import forms
import models


# ----- APPLICATION PARAMETERS ----- #
DEBUG = True
PORT = 8000
HOST = '127.0.0.1'

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'dsadas123fsfdsfdsfds'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# ----- GLOBAL FUNCTIONS ---- #


def invalid_char(test_value, tag=False):
    """
    Function to test for anything other than letters. For tags
    commas are allowed.
    """
    if tag is True:
        remove_comma = re.sub('[,\s]', "", test_value)
        valid_tag = bool(remove_comma.isalpha())
        return valid_tag
    remove_whtspc = re.sub('[\s]', "", test_value)
    valid_title = bool(remove_whtspc.isalpha())
    return valid_title


# ----- APPLICATION HANDLERS ----- #


@login_manager.user_loader
def load_user(userid):
    """ Login Manager Requirement """
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """ Before each request connect to database """

    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """ After each request close connection to database """
    g.db.close()
    return response


@app.errorhandler(404)
def not_found(error):
    """ Function used to create custom 404 error page. """
    return render_template('404.html', error=error), 404


# ----- APPLICATION ROUTES ----- #
@app.route('/')
def index():
    """ Route for Index - Main Page """
    journal = models.Entry.select().order_by(models.Entry.date_created.desc())
    if current_user in models.User.select():
        user = current_user
        return render_template('index.html', journal=journal, user=user)
    return render_template('index.html', journal=journal)


@app.route('/entries/<string:entry>/delete', methods=['GET', 'POST'])
@login_required
def delete(entry):
    """
    Route for deletion of an entry in the database. URL path is
    derived from the slugified title of the entry. Users are
    only able to delete their own entries.
    """
    choice = None
    user = g.user
    rev_slug = entry.replace('-', ' ')
    try:
        delete_entry = models.Entry.get(models.Entry.title ** rev_slug)
    except models.DoesNotExist:
        abort(404)
    if delete_entry.user != user:
        flash("You are not Authorized to Delete that Entry", "errors")
        return redirect(url_for('details', entry=entry))
    if request.method == 'POST':
        try:
            choice = request.form['choice']
            if choice == 'Yes':
                delete_entry.delete_instance()
                flash(f"{delete_entry.title} Successfully Deleted", "success")
            if choice == 'No':
                return redirect(url_for('details', entry=entry))
        except ValueError:
            flash(f'Error Deleting {delete_entry.title}', "errors")
        return redirect(url_for('entries'))
    return render_template('delete.html', choice=choice, rev_slug=rev_slug)


@app.route('/entries/<string:entry>/edit/<string:value>',
           methods=['GET', 'POST'])
@login_required
def edit(entry, value):
    """
    Route for editing a selected entry in the database. Users are only
    able to edit their own entries. URL path derived from Slugified title
    of the entry and the selected column in the table obtained from template.
    """
    user = g.user
    rev_slug = entry.replace('-', ' ')
    try:
        edit_entry = models.Entry.get(models.Entry.title ** rev_slug)
    except models.DoesNotExist:
        abort(404)
    if edit_entry.user != user:
        flash("You are not Authorized to make Changes to that Entry", "errors")
        return redirect(url_for('index'))
    else:
        if request.method == 'POST':
            try:
                if value == 'date':
                    date_format = datetime.datetime.strptime(
                        request.form['editValue'],
                        '%Y-%m-%d').date()
                    edit_entry.date = date_format
                if value == 'title':
                    if invalid_char(request.form['editValue']) is False:
                        flash('Invalid Character Used', "errors")
                        return redirect(url_for('edit',
                                                entry=entry,
                                                value=value))
                    else:
                        edit_entry.title = request.form['editValue']
                if value == 'time_spent':
                    edit_entry.time_spent = request.form['editValue']
                if value == 'learned':
                    edit_entry.learned = request.form['editValue']
                if value == 'resources':
                    edit_entry.resources = request.form['editValue']
                if value == 'tags':
                    if invalid_char(request.form['editValue'],
                                    tag=True) is False:
                        flash('Invalid Character Used', "errors")
                        return redirect(url_for('edit',
                                                entry=entry,
                                                value=value))
                    else:
                        edit_entry.tags = request.form['editValue']
                edit_entry.save()
                flash(f'{rev_slug.upper()} Updated Successfully', "success")
                return redirect(url_for('details', entry=edit_entry.title))
            except ValueError:
                flash("Update Failed", "errors")
                return redirect(url_for('edit', entry=entry, value=value))
    return render_template('edit.html', value=value, edit_entry=edit_entry)


@app.route('/entries')
@login_required
def entries():
    """ Route to display current user's entries """
    if current_user in models.User.select():
        user = g.user
        journal = user.user_journal()
        return render_template('entries.html', journal=journal, user=user)
    return render_template('entries.html')


@app.route('/entries/<string:entry>')
@login_required
def details(entry):
    """
    Route to view details of specific entry. URL path is derived from
    the slugified title of the entry.
    """
    user = g.user
    rev_slug = entry.replace('-', ' ')
    try:
        entry_model = models.Entry.get(models.Entry.title ** rev_slug)
    except models.DoesNotExist:
        abort(404)
    owner = bool(entry_model.user == user)
    return render_template('detail.html',
                           user=user,
                           entry=entry_model,
                           owner=owner)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Route for users to login."""
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.username == form.username.data)
        except models.DoesNotExist:
            flash("Incorrect Username or Password", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login Successful", "success")
                return redirect(url_for('index'))
            else:
                flash("Incorrect Username or Password", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Route to logout user."""
    logout_user()
    return redirect(url_for('index'))


@app.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """
    Route to create new entry. (-) Character is not allowed in the title
    and tags to prevent issues with slugification of values.
    """
    if request.method == 'POST':
        if invalid_char(request.form['title']) is False:
            flash("Invalid Character in Title Used")
            return redirect(url_for('new'))
        if invalid_char(request.form['form_tag'], tag=True) is False:
            flash("Invalid Character in Tags Used")
            return redirect(url_for('new'))
        try:
            date_format = datetime.datetime.strptime(
                request.form['date'], '%Y-%m-%d').date()
            models.Entry.create_entry(
                user=g.user.id,
                tags=request.form['form_tag'].upper(),
                title=request.form['title'],
                date=date_format,
                time_spent=request.form['timeSpent'],
                learned=request.form['whatILearned'],
                resources=request.form['ResourcesToRemember'],
            )
            return redirect(url_for('new'))
        except ValueError:
            flash("Error Creating Entry")

    return render_template('new.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Route for users to register."""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        models.User.create_user(
            username=form.username.data,
            password=form.password.data)
        flash("Registration Successful - Please Log In")
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@app.route('/tags/<string:tag>')
@login_required
def tags(tag):
    """Route to log in users."""
    rev_slug = tag.replace('-', ' ').upper()
    try:
        entries_tagged = models.Entry.select().where(
            models.Entry.tags.contains(rev_slug))
    except models.DoesNotExist:
        abort(404)
    user = g.user
    tagged_journals = user.get_tag_journal(rev_slug)
    return render_template('tags.html',
                           tagged_journals=tagged_journals,
                           user=user, tag=rev_slug,
                           entries_tagged=entries_tagged)


# ----- TEMPLATE FILTERS ----- #


@app.template_filter()
def slugify(text, delim=u'-'):
    """Slugify filter obtained from Slugify documentation."""
    split_word = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
    result = []
    for word in split_word.split(text.lower()):
        result.extend(unidecode(word).split())
    return str(delim.join(result))


@app.template_filter()
def count_filter(tag):
    """ Function to count number of times tag is found"""
    user = g.user
    entry_num = user.get_tag_journal(tag).count()
    return entry_num


@app.template_filter()
def string_filter(string, delimiter=','):
    """
    Function to split tags and resources into seperate values
    by a comma.
    """
    return string.upper().strip().split(delimiter)


if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(username='Admin', password='treehouse')
    except ValueError:
        print('Admin Already Exists')
    app.run(debug=DEBUG, host=HOST, port=PORT)
