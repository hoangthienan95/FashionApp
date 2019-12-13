import random
from typing import List, Tuple

from flask import Flask, render_template

import similarity

app = Flask(__name__)


@app.route('/debug')
def debug_similarity():
    query = similarity.img_paths[random.randint(0, len(similarity.img_paths))]

    results: List[List[Tuple[str, float]]] = []
    for index in [similarity.full_embeddings] + similarity.mask_embeddings:
        results.append(similarity.get_nn_paths(index, query, 100))

    return render_template('debug.html', query=query, results=results)


if __name__ == '__main__':
    app.run()
