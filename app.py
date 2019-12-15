import json
import random
from typing import List, Tuple, Dict

from flask import Flask, render_template, redirect, url_for, session
from flask_session import Session

import similarity
import triplets
from forms import LogInForm, SignUpForm
from tables import db, FashionItem, User

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
with open('config.json') as config_file:
    db_json = json.load(config_file)['database']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        db_json['user'],
        db_json['password'],
        db_json['host'],
        db_json['port'],
        db_json['database']
    )
db.init_app(app)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        similarity.load_all_items(db.session)

with app.app_context():
    similarity.load_primary_indexes(db.session)


USER_ID_KEY = 'user_id'


@app.route('/')
def index():
    if session[USER_ID_KEY] is not None:
        return redirect(url_for('outfits'))

    return redirect(url_for('login'))


@app.route('/login')
def login():
    form = LogInForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username).first()
        if user is not None:
            session[USER_ID_KEY] = user.id
            return redirect(url_for('index'))

        form.username.errors.append('Unknown user.')

    return render_template('', form=form)


@app.route('/logout')
def logout():
    if USER_ID_KEY in session:
        session.pop(USER_ID_KEY)

    return redirect(url_for('/'))


@app.route('/signup')
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username).first()
        if user is None:
            user = User(username=form.username)
            db.session.add(user)
            db.commit()

            session[USER_ID_KEY] = user.id
            return redirect(url_for('index'))

        form.username.errors.append('That username is taken.')

    return render_template('', form=form)


@app.route('/wardrobe')
def wardrobe():
    pass


@app.route('/outfits')
def outfits():
    pass


@app.route('/creator')
def outfit_creator():
    pass


@app.route('/api/add_outfit_item')
def api_add_outfit_item():
    pass


@app.route('/api/remove_outfit_item')
def api_remove_outfit_item():
    pass


@app.route('/api/create_outfit')
def api_create_outfit():
    pass


@app.route('/api/delete_outfit')
def api_delete_outfit():
    pass


@app.route('/api/recommend')
def api_recommend():
    pass


@app.route('/debug')
def debug_similarity():
    query = db.session.query(FashionItem).filter(FashionItem.id == random.randint(0, 100000)).first()

    results: List[List[Tuple[str, float]]] = []
    category_results: List[Dict[str, List[Tuple[str, float]]]] = []
    for ind in similarity.PRIMARY_INDEXES:
        results.append(similarity.get_nn_paths(db.session, ind, query, 5))
        category_results.append(similarity.get_nns_by_category(db.session, ind, query, 1))

    return render_template('debug.html', query=query, results=results, category_results=category_results)


@app.route('/triplets')
def view_triplets():
    return render_template('triplets.html', triplets=triplets.get_triplets(1000))
