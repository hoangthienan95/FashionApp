import json
import os
import random
from typing import List, Tuple, Dict, NamedTuple

from flask import Flask, render_template, redirect, url_for, session, request, jsonify, abort
from flask_session import Session

import similarity
import triplets
from forms import LogInForm, SignUpForm
from tables import db, FashionItem, User, Outfit

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
with open('config.json') as config_file:
    config_json = json.load(config_file)

    db_json = config_json['database']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        db_json['user'],
        db_json['password'],
        db_json['host'],
        db_json['port'],
        db_json['database']
    )

    app.config['SECRET_KEY'] = config_json['secret_key']
db.init_app(app)

with app.app_context():
    db.create_all()

    if __name__ == '__main__':
        similarity.load_all_items(db.session)

with app.app_context():
    similarity.load_primary_indexes(db.session)

USER_ID_KEY = 'user_id'


@app.route('/')
def index():
    if USER_ID_KEY in session:
        return redirect(url_for('wardrobe'))

    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user is not None:
            session[USER_ID_KEY] = user.id
            return redirect(url_for('index'))

        form.username.errors.append('Unknown user.')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    if USER_ID_KEY in session:
        session.pop(USER_ID_KEY)

    return redirect(url_for('index'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user is None:
            user = User(username=form.username.data)
            db.session.add(user)
            db.session.commit()

            session[USER_ID_KEY] = user.id
            return redirect(url_for('index'))

        form.username.errors.append('That username is taken.')

    return render_template('signup.html', form=form)


def item_from_path(path: str) -> FashionItem:
    item_name = os.path.splitext(os.path.basename(path))[0]
    return db.session.query(FashionItem).filter(FashionItem.name == item_name).one()


@app.route('/wardrobe')
def wardrobe():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    return render_template('wardrobe.html',
                           username=user.username,
                           user_wardrobe=user.wardrobe_items)


@app.route('/randomize-wardrobe')
def randomize_wardrobe():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    if len(user.wardrobe_items) > 0:
        abort(400)

    random_ids = random.sample(list(range(0, 250000)), random.randrange(200, 300))

    random_items = db.session.query(FashionItem).filter(FashionItem.id.in_(random_ids)).all()
    for item in random_items:
        user.wardrobe_items.append(item)
    db.session.commit()

    return redirect(url_for('wardrobe'))


@app.route('/outfits')
def outfits():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    return render_template('outfits.html',
                           username=user.username,
                           outfits=user.outfits)


@app.route('/creator')
def outfit_creator():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    return render_template('outfit_creator.html',
                           username=user.username,
                           user_wardrobe=user.wardrobe_items,
                           categories=similarity.MERGED_CATEGORIES)


@app.route('/api/add_outfit_item')
def api_add_outfit_item():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()

    item = item_from_path(request.json['item_path'])

    user.items.append(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item_id': item.id
    })


@app.route('/api/remove_outfit_item')
def api_remove_outfit_item():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()

    item = item_from_path(request.json['item_path'])

    if item not in user.items:
        abort(400)

    user.items.remove(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item_id': item.id
    })


@app.route('/api/create_outfit', methods=['POST'])
def api_create_outfit():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    items = db.session.query(FashionItem).filter(FashionItem.id.in_(request.json['items'])).all()

    outfit = Outfit(
        name=request.json['name'] if 'name' in request.json else 'Untitled',
        items=items
    )

    user.outfits.append(outfit)
    db.session.commit()

    return jsonify({
        'success': True,
        'outfit_id': outfit.id,
        'item_ids': [item.id for item in outfit.items]
    })


@app.route('/api/delete_outfit')
def api_delete_outfit():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    outfit = db.session.query(Outfit).filter(Outfit.id == request.json['outfit_id']).one()

    if outfit not in user.outfits:
        abort(400)

    db.session.delete(outfit)
    db.session.commit()

    return jsonify({
        'success': True
    })


@app.route('/api/recommend', methods=['POST'])
def api_recommend():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    query_item = db.session.query(FashionItem).filter(FashionItem.id == request.json['item_id']).one()

    mask_i = random.randrange(1, 5)
    if request.json['wardrobe']:
        wardrobe_indexes = similarity.create_indexes(user.wardrobe_items)

        results = similarity.get_nns_by_category(
            session=db.session,
            index=wardrobe_indexes[mask_i],
            query=query_item,
            results_per_category=100,
            num_neighbors=min(1000, len(user.wardrobe_items))
        )
    else:
        results = similarity.get_nns_by_category(
            session=db.session,
            index=similarity.PRIMARY_INDEXES[mask_i],
            query=query_item,
            results_per_category=1,
            num_neighbors=min(1000, len(user.wardrobe_items))
        )

    results_json = []
    for cat, cat_results in results.items():
        for item, score in cat_results:
            results_json.append({
                'id': item.id,
                'path': item.get_path(),
                'category': item.merged_category()
            })

    return jsonify({
        'results': results_json
    })


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
