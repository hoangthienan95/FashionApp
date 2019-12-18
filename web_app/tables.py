import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


user_items = db.Table(
    'user_items',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('fashion_items.id'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)

    wardrobe_items = db.relationship('FashionItem', secondary=user_items, lazy=True)
    outfits = db.relationship('Outfit', back_populates='user', lazy=True)


class FashionItem(db.Model):
    __tablename__ = 'fashion_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    semantic_category = db.Column(db.String(100), nullable=False)

    full_embedding = db.Column(db.String(2000), nullable=False)
    mask_1_embedding = db.Column(db.String(2000), nullable=False)
    mask_2_embedding = db.Column(db.String(2000), nullable=False)
    mask_3_embedding = db.Column(db.String(2000), nullable=False)
    mask_4_embedding = db.Column(db.String(2000), nullable=False)

    def get_path(self) -> str:
        return os.path.join('static/images', self.name + '.jpg')

    def merged_category(self) -> str:
        c = self.semantic_category
        if c in ['scarves', 'sunglasses', 'jewellery']:
            c = 'accessories'
        elif c == 'outerwear':
            c = 'tops'
        return c


outfit_items = db.Table(
    'outfit_items',
    db.Column('outfit_id', db.Integer, db.ForeignKey('outfits.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('fashion_items.id'), primary_key=True)
)


class Outfit(db.Model):
    __tablename__ = 'outfits'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    user = db.relationship('User', back_populates='outfits')
    items = db.relationship('FashionItem', secondary=outfit_items, lazy=False)
