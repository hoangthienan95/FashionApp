import json
import os
import random
from typing import List, Tuple, Sequence, Dict

from flask import Flask, render_template

import similarity
import tables
import triplets

app = Flask(__name__)
with open('config.json') as config_file:
    db_json = json.load(config_file)['database']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
        db_json['user'],
        db_json['password'],
        db_json['host'],
        db_json['port'],
        db_json['database']
    )
tables.db.init_app(app)

with app.app_context():
    tables.db.create_all()


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


if __name__ == '__main__':
    app.run()
