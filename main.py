from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["FLASK_SECRET_KEY_TOP_10_MOVIES"]
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top_10_movies_website.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)

API_KEY = os.environ["THE_MOVIEDB_API_KEY"]
MOVIES_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_ID_SEARCH_URL = "https://api.themoviedb.org/3/movie/"
POSTER_URL = "https://image.tmdb.org/t/p/w500"


class Edit_Form(FlaskForm):
    rating = StringField(label="Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label="Done")


class Add_Form(FlaskForm):
    new_movie = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(500), nullable=True)
    img_url = db.Column(db.String(300), unique=True, nullable=False)

    def __repr__(self):
        return f'<Movie name - {self.title}>'


@app.route("/")
def home():
    all_cards = Movies.query.order_by(Movies.rating).all()
    number_of_cards = len(all_cards)
    for card in all_cards:
        card.ranking = number_of_cards
        number_of_cards -= 1
        db.session.commit()
    return render_template("index.html", cards=all_cards)


@app.route("/update", methods=["POST", "GET"])
def update_info():
    edit_form = Edit_Form()
    movie_title = request.args.get("title")
    if edit_form.validate_on_submit():
        new_rating = edit_form.data.get("rating")
        new_review = edit_form.data.get("review")
        current_id = request.args.get("id")
        current_card = Movies.query.get(current_id)
        current_card.rating = new_rating
        current_card.review = new_review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=edit_form, title=movie_title)


@app.route("/delete")
def card_delete():
    card_id = request.args.get('card_id')
    current_card = Movies.query.get(card_id)
    db.session.delete(current_card)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["POST", "GET"])
def add_movie():
    add_form = Add_Form()
    if add_form.validate_on_submit():
        params = {
            'api_key': f"{API_KEY}",
            'query': f"{add_form.data.get('new_movie')}"
        }
        response = requests.get(f"{MOVIES_SEARCH_URL}", params=params)
        found_movies = response.json()
        return render_template("select.html", movies=found_movies)
    return render_template("add.html", form=add_form)


@app.route("/get_info")
def movie_info():
    movie_id = request.args.get('id')
    params = {
        'api_key': f"{API_KEY}",
    }
    response = requests.get(f"{MOVIE_ID_SEARCH_URL}{movie_id}", params=params)
    movie_data = response.json()

    title = movie_data['title']
    year = movie_data['release_date'].split("-")[0]
    description = movie_data['overview']
    poster_url = f"{POSTER_URL}" + movie_data['poster_path']

    new_movie = Movies(title=title, img_url=poster_url, year=year, description=description)

    db.session.add(new_movie)
    db.session.commit()

    return redirect(url_for('update_info', id=new_movie.id, title=new_movie.title))


if __name__ == '__main__':
    app.run(debug=True)
