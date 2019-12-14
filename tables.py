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


class FashionItem(db.Model):
    __tablename__ = 'fashion_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    embeddings = db.relationship('ItemEmbedding', order_by='ItemEmbedding.mask', lazy=False)


class ItemEmbedding(db.Model):
    __tablename__ = 'embeddings'

    item_id = db.Column(db.Integer, db.ForeignKey('fashion_items.id'), nullable=False)
    mask = db.Column(db.Integer, nullable=False)
    vector = db.Column(db.String(2500), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint(item_id, mask),
    )


outfit_items = db.Table(
    'outfit_items',
    db.Column('outfit_id', db.Integer, db.ForeignKey('outfits.id'), primary_key=True),
    db.Column('item_id', db.Integer, db.ForeignKey('fashion_items.id'), primary_key=True)
)


class Outfit(db.Model):
    __tablename__ = 'outfits'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

    items = db.relationship('FashionItem', secondary=outfit_items, lazy=False)
