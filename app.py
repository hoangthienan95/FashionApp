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

application = Flask(__name__)

application.config['SESSION_TYPE'] = 'filesystem'
Session(application)

application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
with open('config.json') as config_file:
    config_json = json.load(config_file)

    db_json = config_json['database']
    application.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        db_json['user'],
        db_json['password'],
        db_json['host'],
        db_json['port'],
        db_json['database']
    )

    application.config['SECRET_KEY'] = config_json['secret_key']
db.init_app(application)

with application.app_context():
    db.create_all()

    if __name__ == '__main__':
        similarity.load_all_items(db.session)

with application.app_context():
    similarity.load_primary_indexes(db.session)

USER_ID_KEY = 'user_id'


@application.route('/')
def index():
    if USER_ID_KEY in session:
        return redirect(url_for('wardrobe'))

    return redirect(url_for('login'))


@application.route('/login', methods=['GET', 'POST'])
def login():
    form = LogInForm()

    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user is not None:
            session[USER_ID_KEY] = user.id
            return redirect(url_for('index'))

        form.username.errors.append('Unknown user.')

    return render_template('login.html', form=form)


@application.route('/logout')
def logout():
    if USER_ID_KEY in session:
        session.pop(USER_ID_KEY)

    return redirect(url_for('index'))


@application.route('/signup', methods=['GET', 'POST'])
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


def by_category(items: List[FashionItem]) -> Dict[str, FashionItem]:
    items_by_category = {k: [] for k in similarity.MERGED_CATEGORIES}
    for item in items:
        items_by_category[item.merged_category()].append(item)

    return items_by_category


@application.route('/wardrobe')
def wardrobe():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    return render_template('wardrobe.html',
                           username=user.username,
                           user_wardrobe=user.wardrobe_items,
                           wardrobe_by_category=by_category(user.wardrobe_items))


@application.route('/randomize-wardrobe')
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


@application.route('/outfits')
def outfits():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    return render_template('outfits.html',
                           username=user.username,
                           user=user,
                           outfits=user.outfits)


@application.route('/creator')
def outfit_creator():
    if USER_ID_KEY not in session:
        return redirect('/')

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    return render_template('outfit_creator.html',
                           username=user.username,
                           user_wardrobe=user.wardrobe_items,
                           wardrobe_by_category=by_category(user.wardrobe_items),
                           categories=similarity.MERGED_CATEGORIES)


@application.route('/api/add_wardrobe_item', methods=['POST'])
def api_add_wardrobe_item():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    item = db.session.query(FashionItem).filter(FashionItem.id == request.json['item_id']).one()

    if item in user.wardrobe_items:
        abort(400)

    user.wardrobe_items.append(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item_id': item.id
    })


@application.route('/api/remove_wardrobe_item', methods=['POST'])
def api_remove_wardrobe_item():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    item = db.session.query(FashionItem).filter(FashionItem.id == request.json['item_id']).one()

    if item not in user.wardrobe_items:
        abort(400)

    user.wardrobe_items.remove(item)
    db.session.commit()

    return jsonify({
        'success': True,
        'item_id': item.id
    })


@application.route('/api/create_outfit', methods=['POST'])
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


@application.route('/api/delete_outfit', methods=['POST'])
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


@application.route('/api/recommend', methods=['POST'])
def api_recommend():
    if USER_ID_KEY not in session:
        abort(403)

    user = db.session.query(User).filter(User.id == session[USER_ID_KEY]).one()
    query_item = db.session.query(FashionItem).filter(FashionItem.id == request.json['item_id']).one()

    if request.json['wardrobe'] == 'random':
        request.json['wardrobe'] = random.choice((True, False))

    results_per_category = random.randrange(1, 3)

    mask_i = random.randrange(1, 5)
    if request.json['wardrobe']:
        wardrobe_indexes = similarity.create_indexes(user.wardrobe_items)

        results = similarity.get_nns_by_category(
            session=db.session,
            index=wardrobe_indexes[mask_i],
            query=query_item,
            results_per_category=results_per_category,
            num_neighbors=min(1000, len(user.wardrobe_items))
        )
    else:
        results = similarity.get_nns_by_category(
            session=db.session,
            index=similarity.PRIMARY_INDEXES[mask_i],
            query=query_item,
            results_per_category=results_per_category,
            num_neighbors=min(1000, len(user.wardrobe_items))
        )

    results_json = []
    for cat, cat_results in results.items():
        for item, score in cat_results:
            results_json.append({
                'id': item.id,
                'path': item.get_path(),
                'category': item.merged_category(),
                'in_wardrobe': item in user.wardrobe_items
            })

    return jsonify({
        'results': results_json
    })


@application.route('/debug')
def debug_similarity():
    query = db.session.query(FashionItem).filter(FashionItem.id == random.randint(0, 100000)).first()

    results: List[List[Tuple[str, float]]] = []
    category_results: List[Dict[str, List[Tuple[str, float]]]] = []
    for ind in similarity.PRIMARY_INDEXES:
        results.append(similarity.get_nn_paths(db.session, ind, query, 5))
        category_results.append(similarity.get_nns_by_category(db.session, ind, query, 1))

    return render_template('debug.html', query=query, results=results, category_results=category_results)


@application.route('/triplets')
def view_triplets():
    return render_template('triplets.html', triplets=triplets.get_triplets(1000))
