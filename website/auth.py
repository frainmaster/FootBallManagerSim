from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user
import re

auth = Blueprint('auth', __name__)


def is_email(email: str) -> bool:
    email_re = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return bool(re.fullmatch(email_re, email))


def is_username_allowed(username: str) -> bool:
    username = username.replace("_", "").replace(".", "")
    return username.isalnum()


@auth.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        cred = request.form.get('cred')
        password = request.form.get('password')

        if is_email(cred):
            user = User.query.filter_by(email=cred)\
                .first()  # return only the first result, instead of a list
        else:  # enable login with username
            user = User.query.filter_by(username=cred)\
                .first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully.', category="success")
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category="error")
        else:
            flash('Email/username does not exist.', category="error")
    # # redirect to home page to restrict readily logged in user to re-logging in
    # elif request.method == "GET":
    #     if current_user:
    #         flash("You are already logged in.", category="error")
    #         return redirect(url_for("views.home"))
    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required  # enable logout only when a user is logged in
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get('email')
        username = request.form.get('userName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        # check if email or username is taken
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already used.', category="error")
            return render_template("signup.html", user=current_user)
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already used.', category="error")
            return render_template("signup.html", user=current_user)

        # user credentials handling
        if not is_email(email):
            flash('Improper email format.', category="error")
        elif len(username) < 3:
            flash('Username must be greater than 3 characters.', category="error")
        elif not is_username_allowed(username):
            flash('Only alphabets, numbers, underscore (_) and dot (.) is allowed.', category="error")
        elif password1 != password2:
            flash("Passwords don't match.", category="error")
        elif len(password1) < 8:
            flash('Password must be more than 7 characters.', category="error")
        else:
            new_user = User(
                email=email,
                username=username,
                password=generate_password_hash(password1, method="sha256")
            )
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created.', category="success")
            # create team and add players
            return redirect(url_for("views.home"))
    # # redirect to home page to restrict readily logged in user to sign up
    # elif request.method == "GET":
    #     if current_user:
    #         flash("Logout to create a new account", category="error")
    #         return redirect(url_for("views.home"))
    return render_template("signup.html", user=current_user)
