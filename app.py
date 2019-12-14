import json
import os
import random
from typing import List, Tuple, Sequence, Dict

from flask import Flask, render_template

import similarity
import triplets
from tables import db

app = Flask(__name__)
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


@app.route('/debug')
def debug_similarity():
    query = similarity.img_paths[random.randint(0, len(similarity.img_paths))]

    results: List[List[Tuple[str, float]]] = []
    category_results: List[Dict[str, List[Tuple[str, float]]]] = []
    for index in [similarity.full_embeddings] + similarity.mask_embeddings:
        results.append(similarity.get_nn_paths(index, query, 5))
        category_results.append(similarity.get_nns_by_category(index, query, 1))

    return render_template('debug.html', query=query, results=results, category_results=category_results)


@app.route('/triplets')
def view_triplets():
    return render_template('triplets.html', triplets=triplets.get_triplets(1000))
