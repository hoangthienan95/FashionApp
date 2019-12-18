import json
import os
import time
from typing import Tuple, List, Dict

from annoy import AnnoyIndex
from annoy.annoylib import Annoy
from sqlalchemy.orm import Session, defer

from tables import FashionItem

NUM_MASKS = 4
EMBEDDING_SIZE = 64
DISTANCE_FUNCTION = 'angular'
NUM_TREES = 10

IMAGES_DIR = 'static/images'
EMBEDDINGS_DIR = 'data/embeddings'
INDEXES_DIR = 'data/annoy_indexes'
ANNOY_EXT = '.ann'
IMAGE_EXT = '.jpg'

ITEM_METADATA_FILE_PATH = 'data/item_metadata.json'
CATEGORIES_FILE_PATH = 'data/categories.csv'

MERGED_CATEGORIES = [
    'hats',
    'all-body',
    'tops',
    'bottoms',
    'shoes',
    'bags',
    'accessories'
]
MERGED_CATEGORIES_DISPLAY = [
    'Hats',
    'Full-Body',
    'Tops',
    'Bottoms',
    'Shoes',
    'Bags',
    'Accessories'
]

def load_all_items(session: Session):
    print('Loading all items.')
    categories: Dict[int, str] = {}

    with open(CATEGORIES_FILE_PATH) as categories_file:
        for line in categories_file:
            cat_id, name, _ = line.strip('\n').split(',')
            cat_id = int(cat_id)

            categories[cat_id] = name

    items: Dict[str, Tuple[str, str, List[str]]] = {}

    with open(ITEM_METADATA_FILE_PATH) as metadata_file:
        metadata_json: Dict = json.load(metadata_file)

        for item_name, item_json in metadata_json.items():
            cat = categories[int(item_json['category_id'])]
            semantic_cat = item_json['semantic_category']

            items[item_name] = (cat, semantic_cat, [])

    embeddings_paths = ['full_embeddings.csv'] + ['mask_{}_embeddings.csv'.format(i + 1) for i in range(NUM_MASKS)]
    embeddings_paths = [os.path.join(EMBEDDINGS_DIR, p) for p in embeddings_paths]

    for em_path in embeddings_paths:
        with open(em_path) as embeddings_file:
            for line in embeddings_file:
                sp = line.strip('\n').split(', ')
                n = sp[0].strip(IMAGE_EXT)
                v = ','.join(sp[1:])

                try:
                    items[n][2].append(v)
                except KeyError:
                    pass

    print('Creating ORM objects.')
    db_items = []
    for name, (cat, semantic_cat, embeddings) in items.items():
        db_items.append(FashionItem(
            name=name,
            category=cat,
            semantic_category=semantic_cat,
            full_embedding=embeddings[0],
            mask_1_embedding=embeddings[1],
            mask_2_embedding=embeddings[2],
            mask_3_embedding=embeddings[3],
            mask_4_embedding=embeddings[4]
        ))

    print('Inserting items.')
    start_time = time.time()
    session.bulk_save_objects(db_items)
    session.commit()
    print('Finished inserting items (took {:.2f}s)'.format(time.time() - start_time))


def create_indexes(items: List[FashionItem]):
    indexes: List[Annoy] = [Annoy(EMBEDDING_SIZE, DISTANCE_FUNCTION) for i in range(NUM_MASKS + 1)]

    for item in items:
        em_l = [
            item.full_embedding,
            item.mask_1_embedding,
            item.mask_2_embedding,
            item.mask_3_embedding,
            item.mask_4_embedding
        ]
        for ind, em in zip(indexes, em_l):
            vec = [float(v) for v in em.split(',')]
            ind.add_item(item.id, vec)

    for ind in indexes:
        ind.build(NUM_TREES)

    return indexes


PRIMARY_INDEXES: List[Annoy] = []


def load_primary_indexes(session: Session):
    if not os.path.exists(INDEXES_DIR):
        os.mkdir(INDEXES_DIR)

    global PRIMARY_INDEXES
    save_names = ['full_index'] + ['mask_{}_index'.format(i + 1) for i in range(NUM_MASKS)]
    save_paths = [os.path.join(INDEXES_DIR, n + ANNOY_EXT) for n in save_names]

    if False not in [os.path.exists(p) for p in save_paths]:
        print('Loading primary indexes.')
        PRIMARY_INDEXES = [AnnoyIndex(EMBEDDING_SIZE, DISTANCE_FUNCTION) for i in range(NUM_MASKS + 1)]
        for ind, p in zip(PRIMARY_INDEXES, save_paths):
            ind.load(p)
        return

    print('Creating primary indexes.')
    items: List[FashionItem] = session.query(FashionItem).order_by(FashionItem.id).all()
    print('Loaded items.')

    indexes = create_indexes(items)

    for ind, path in zip(indexes, save_paths):
        ind.save(path)

    PRIMARY_INDEXES = indexes
    print('Saved primary indexes.')


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


def get_nn_paths(session: Session, index: Annoy, query: FashionItem,
                 num_results: int) -> List[Tuple[FashionItem, float]]:
    # The nearest neighbor search often includes the item itself as the first result,
    # so an extra result is included and the query item is removed from the results
    results = index.get_nns_by_item(query.id, num_results + 1, include_distances=True)
    results = [r for r in zip(*results) if r[0] != query.id]
    results = results[0:num_results]  # Slice the results in case the query item was not included
    result_ids = [r[0] for r in results]

    result_items = session.query(FashionItem).filter(FashionItem.id.in_(result_ids))\
        .options(
            defer(FashionItem.full_embedding),
            defer(FashionItem.mask_1_embedding),
            defer(FashionItem.mask_2_embedding),
            defer(FashionItem.mask_3_embedding),
            defer(FashionItem.mask_4_embedding)
        ).all()

    return list(zip(result_items, [r[1] for r in results]))


def get_nns_by_category(session: Session, index: Annoy, query: FashionItem, results_per_category: int,
                        num_neighbors: int = 1000,
                        for_categories: List[str] = None) -> Dict[str, List[Tuple[FashionItem, float]]]:
    if for_categories is None:
        for_categories = MERGED_CATEGORIES

    results: Dict[str, List[Tuple[FashionItem, float]]] = {c: [] for c in for_categories}
    num_filled = 0

    for item, score in get_nn_paths(session, index, query, num_neighbors):
        if num_filled >= len(for_categories):
            break

        c_list = results[item.merged_category()]
        if len(c_list) < results_per_category:
            c_list.append((item, score))
            if len(c_list) >= results_per_category:
                num_filled += 1

    return results
