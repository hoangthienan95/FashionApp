import json
import os
from typing import Tuple, List, Dict

from annoy import AnnoyIndex
from annoy.annoylib import Annoy

NUM_MASKS = 4
EMBEDDING_SIZE = 64

IMAGES_DIR = 'static/images'
EMBEDDINGS_DIR = 'data/embeddings'
INDEXES_DIR = 'data/annoy_indexes'
ANNOY_EXT = '.ann'
IMAGE_EXT = '.jpg'

ITEM_METADATA_FILE_PATH = 'data/item_metadata.json'


def get_index(embeddings_path: str, embedding_size: int, load_paths: bool = False) -> Tuple[Annoy, List[str]]:
    if not os.path.exists(INDEXES_DIR):
        os.mkdir(INDEXES_DIR)

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
        cur_i = 0
        for line in embeddings_file:
            values = line.strip('\n').split(', ')
            p = os.path.join(IMAGES_DIR, values[0])

            if p not in item_categories:
                continue  # Skip items with missing categories (about 10,000)

            if load_paths:
                file_paths.append(p)

            if not loaded:
                em = [float(v) for v in values[1:]]
                index.add_item(cur_i, em)
            cur_i += 1

    if not loaded:
        index.build(10)
        index.save(index_path)
        print('Created and saved index {}'.format(index_path))

    return index, file_paths


def load_categories() -> Tuple[List[str], Dict[str, str]]:
    categories_set = set()
    item_categories_dict: Dict[str, str] = {}

    with open(ITEM_METADATA_FILE_PATH) as metadata_file:
        metadata_json: Dict = json.load(metadata_file)

        for item_name, item_json in metadata_json.items():
            p = os.path.join(IMAGES_DIR, item_name + IMAGE_EXT)

            c = item_json['semantic_category']
            categories_set.add(c)
            item_categories_dict[p] = c

    cat = sorted(list(categories_set))
    print('Loaded {} items from {} categories: {}'.format(len(item_categories_dict), len(cat), cat))
    return cat, item_categories_dict


categories, item_categories = load_categories()
full_embeddings, img_paths = get_index('data/embeddings/full_embeddings.csv', 64, load_paths=True)
mask_embeddings = [get_index(os.path.join(EMBEDDINGS_DIR,
                                          'mask_{}_embeddings.csv'.format(i + 1)),
                             EMBEDDING_SIZE)[0] for i in range(NUM_MASKS)]


def get_nn_paths(index: Annoy, query: str, num_results: int) -> List[Tuple[str, float]]:
    query_index = img_paths.index(query)
    # The nearest neighbor search often includes the item itself as the first result,
    # so an extra result is included and the query item is removed from the results
    results = index.get_nns_by_item(query_index, num_results + 1, include_distances=True)
    results = [(img_paths[r[0]], r[1]) for r in zip(*results) if r[0] != query_index]
    results = results[0:num_results]  # Slice the results in case the query item was not included

    return results


def get_nns_by_category(index: Annoy, query: str, results_per_category: int,
                        for_categories: List[str] = None) -> Dict[str, List[Tuple[str, float]]]:
    if for_categories is None:
        for_categories = categories

    num_results = 50000
    results: Dict[str, List[Tuple[str, float]]] = {c: [] for c in for_categories}
    num_filled = 0

    for p, s in get_nn_paths(index, query, num_results):
        if num_filled >= len(for_categories):
            break
        c = item_categories[p]

        c_list = results[c]
        if len(c_list) < results_per_category:
            c_list.append((p, s))
            if len(c_list) >= results_per_category:
                num_filled += 1

    return results
