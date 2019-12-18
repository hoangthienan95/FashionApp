import itertools
import json
from typing import List

import pandas as pd
from pandas import DataFrame

LABEL_DESCRIPTIONS_PATH = '../data/iMaterialist/label_descriptions.json'
TRAIN_DATA_PATH = '../data/iMaterialist/train.csv'

ENCODED_SAVE_PATH = '../data/iMaterialist/encoded_attributes.csv'
PAIRS_TRAIN_SAVE_PATH = '../data/iMaterialist/pairs_train.csv'
PAIRS_TEST_SAVE_PATH = '../data/iMaterialist/pairs_test.csv'


def encode_attributes():
    with open(LABEL_DESCRIPTIONS_PATH) as desc_file:
        descriptions_json = json.load(desc_file)

        categories = [c['name'] for c in descriptions_json['categories']]
        attributes = [a['name'] for a in descriptions_json['attributes']]

        print(categories)
        print(attributes)
        print('num categories: {}, num attributes: {}'.format(len(categories), len(attributes)))

    data = pd.read_csv(TRAIN_DATA_PATH)

    print(data.columns)
    print(data.head())
    print(data.shape)

    print('Encoding attributes...')
    encoded_data_list = []
    for i, data_row in data.iterrows():
        class_id_split = data_row.ClassId.split('_')
        if len(class_id_split) > 1:
            encoded_category = [0] * len(categories)
            encoded_attributes = [0] * len(attributes)

            encoded_category[int(class_id_split[0])] = 1

            for a_i in class_id_split[1:]:
                encoded_attributes[int(a_i)] = 1
            encoded_data_list.append(
                [data_row.ImageId] + encoded_category + encoded_attributes
            )

    encoded_cols = ['image_id'] + categories + attributes
    encoded_data = DataFrame(data=encoded_data_list, columns=encoded_cols)

    print('Encoded attributes:')
    print(encoded_data.head())

    def count_rows(name: str, col_names: List[str], drop_below: int, drop_rows: bool):
        rows_per_col = sorted(
            [(c, encoded_data[c].sum()) for c in col_names],
            key=lambda v: v[1],
            reverse=True
        )

        drop_cols = []

        print('Rows per {}:'.format(name))
        for c, row_count in rows_per_col:
            if row_count >= drop_below:
                print('{}: {}'.format(c, row_count))
            else:
                print('{} (DROPPED): {}'.format(c, row_count))
                drop_cols.append(c)

        print()
        if drop_rows:
            indices_to_drop = []
            for c in drop_cols:
                indices_to_drop += list(
                    encoded_data.index[encoded_data[c] == 1].values
                )
            encoded_data.drop(index=indices_to_drop, inplace=True)
            print('Dropped {} rows'.format(len(indices_to_drop)))

        encoded_data.drop(columns=drop_cols, inplace=True)
        print('Dropped {} {} columns\n'.format(len(drop_cols), name))

    count_rows('category', categories, drop_below=90, drop_rows=True)
    count_rows('attribute', attributes, drop_below=300, drop_rows=False)

    print('Final encoded attributes:')
    print(encoded_data.head())

    encoded_data.to_csv(ENCODED_SAVE_PATH)
    print('Encoded attributes saved at {}'.format(ENCODED_SAVE_PATH))

    print('Finding pairs')

    pairs_cols = [str(i) + '_' + c for i in range(2) for c in encoded_data.columns.values.tolist()]

    num_images = 0
    num_ignored = 0

    encoded_pairs_list: List[List] = []
    for image_id in encoded_data['image_id'].unique():
        num_images += 1

        image_items = encoded_data.loc[encoded_data['image_id'] == image_id]

        if len(image_items) > 1:
            for (pair_0, pair_1) in itertools.combinations(image_items.values.tolist(), 2):
                encoded_pairs_list.append(pair_0 + pair_1)
        else:
            num_ignored += 1

    encoded_pairs = DataFrame(data=encoded_pairs_list, columns=pairs_cols)

    print('Found {} pairs from {} unique images ({} images had only one item)'.format(
        len(encoded_pairs_list),
        num_images,
        num_ignored
    ))

    print('\nPairs:')
    print(encoded_pairs)

    pairs_train = encoded_pairs.sample(frac=0.8, random_state=100)
    pairs_test = encoded_pairs.drop(index=pairs_train.index)

    print('\nPairs train:')
    print(pairs_train)
    print('\nPairs test:')
    print(pairs_test)

    pairs_train.to_csv(PAIRS_TRAIN_SAVE_PATH)
    pairs_test.to_csv(PAIRS_TEST_SAVE_PATH)
    print('Pairs train saved at {}'.format(PAIRS_TRAIN_SAVE_PATH))
    print('Pairs test saved at {}'.format(PAIRS_TEST_SAVE_PATH))


if __name__ == '__main__':
    encode_attributes()
