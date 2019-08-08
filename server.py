"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from model import User, Rating, Movie, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    return render_template("homepage.html")


@app.route('/users')
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)

@app.route('/register')
def register_form():
    """Displays registration form"""

    return render_template("register_form.html")

@app.route('/register', methods=["POST"])
def register_process():
    """Add new user to database"""

    new_user_email = request.form.get("email")
    new_user_password = request.form.get("password")
    age = request.form.get("age")
    zipcode = request.form.get("zipcode")

    if User.query.filter(User.email==new_user_email).all() == []:
        new_user = User(email=new_user_email, 
                        password=new_user_password, 
                        age=age,
                        zipcode=zipcode
                        )

        db.session.add(new_user)
        db.session.commit()

    return redirect("/login")

@app.route('/login')
def display_login():
    """Display login form"""

    return render_template("login.html")

@app.route('/check_login')
def check_credentials():
    """Handles submission of log in form."""

    user_email = request.args.get("email")
    user_password = request.args.get("password")
    user_object = User.query.filter(User.email==user_email, User.password==user_password).all()
    user_id = user_object[0].user_id

    if user_object:
        session['user_id'] = user_id
        flash("You are now logged in!")
        return redirect("/users/"+str(user_id))

    elif User.query.filter(User.email==user_email, User.password!=user_password).all():
        flash("Incorrect password. Try again!")
        return redirect("/login")
    else:
        flash("Email address is not recognized, please register.")
        return redirect("/register")

@app.route('/logout')
def log_user_out():
    """Logs user out"""

    session['user_id'] = None
    flash("You have been logged out.")

    return redirect("/login")


@app.route('/users/<user_id>')
def show_user_information(user_id):
    """Displays all user data"""

    user = User.query.filter(User.user_id==user_id).one()
    ratings = Rating.query.filter(Rating.user_id==user_id).all()

    return render_template("user_info.html", user=user,ratings=ratings)

@app.route('/movies')
def movie_list():
    """Show list of movies."""

    movies = db.session.query(Movie.title, Movie.movie_id).all()
    movies.sort()    
    return render_template("movie_list.html", movies=movies)


@app.route('/movies/<movie_id>')
def display_movie_info(movie_id):
    """Displays information about the movie"""

    movie = Movie.query.filter(Movie.movie_id==movie_id).one()
    ratings = Rating.query.filter(Rating.movie_id==movie_id).all()

    return render_template("movie_info.html", movie=movie, ratings=ratings)

@app.route('/movies/<movie_id>', methods=["POST"])
def handleUserRating(movie_id):
    """Takes user rating and checks/adds it to database"""
    user_rating = request.form.get("rating")
    current_user_id = session['user_id']

    if current_user_id is None:
        flash("Only logged in users may rate a movie.")

    else:
        try:
            rating = Rating.query.filter(Rating.user_id==current_user_id, 
                                        Rating.movie_id==movie_id).one()
            rating.score = user_rating
            db.session.commit()
            flash("Your rating has been updated!")
        except:
            new_rating = Rating(movie_id=movie_id, 
                                user_id=current_user_id, 
                                score=user_rating)
            db.session.add(new_rating)
            db.session.commit()
            flash("Your rating has been added!")

    return redirect('/movies')

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    # make sure templates, etc. are not cached in debug mode
    app.jinja_env.auto_reload = app.debug

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(port=5000, host='0.0.0.0')
