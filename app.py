import os
import random
from typing import List, Tuple, Sequence, Dict

from flask import Flask, render_template

import similarity
import triplets

app = Flask(__name__)


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
