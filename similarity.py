import os
from typing import Tuple, List

from annoy import AnnoyIndex
from annoy.annoylib import Annoy

NUM_MASKS = 4
EMBEDDING_SIZE = 64

IMAGES_DIR = 'static/images'
EMBEDDINGS_DIR = 'data/embeddings'
INDEXES_DIR = 'data/annoy_indexes'
ANNOY_EXT = '.ann'


def get_index(embeddings_path: str, embedding_size: int, load_paths: bool = False) -> Tuple[Annoy, List[str]]:
    embeddings_name = os.path.splitext(os.path.basename(embeddings_path))[0]
    index_path = os.path.join(INDEXES_DIR, embeddings_name + ANNOY_EXT)

    index = AnnoyIndex(embedding_size, 'euclidean')
    if os.path.exists(index_path):
        print('Loaded index {}'.format(index_path))
        index.load(index_path)
        loaded = True

        if not load_paths:
            return index, []
    else:
        loaded = False

    file_paths = []

    with open(embeddings_path) as embeddings_file:
        for i, l in enumerate(embeddings_file):
            values = l.strip('\n').split(', ')
            p = os.path.join(IMAGES_DIR, values[0])

            if load_paths:
                file_paths.append(p)

            if not loaded:
                em = [float(v) for v in values[1:]]
                index.add_item(i, em)

    if not loaded:
        index.build(10)
        index.save(index_path)
        print('Created and saved index {}'.format(index_path))

    return index, file_paths


def get_nn_paths(index: Annoy, query: str, num_results: int) -> List[Tuple[str, float]]:
    query_index = img_paths.index(query)
    results = index.get_nns_by_item(query_index, num_results, include_distances=True)

    return [(img_paths[r[0]], r[1]) for r in zip(*results)]


full_embeddings, img_paths = get_index('data/embeddings/full_embeddings.csv', 64, load_paths=True)
mask_embeddings = [get_index(os.path.join(EMBEDDINGS_DIR,
                                          'mask_{}_embeddings.csv'.format(i + 1)),
                             EMBEDDING_SIZE)[0] for i in range(NUM_MASKS)]
