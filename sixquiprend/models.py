from sixquiprend.sixquiprend import app, db
from passlib.hash import bcrypt
import math
import random

class NoSuitableColumnException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return 'User %i must choose a column to replace', value

user_games = db.Table('user_games',
        db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
        db.Column('game_id', db.Integer, db.ForeignKey('game.id'))
)

class User(db.Model):
    BOT_ROLE = 1
    PLAYER_ROLE = 2
    ADMIN_ROLE = 3

    id = db.Column(db.Integer, primary_key=True)
    # User authentication information
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    authenticated = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=app.config['ACTIVATE_ALL_USERS'])
    urole = db.Column(db.Integer, default=PLAYER_ROLE)
    games = db.relationship('Game', secondary=user_games,
            backref=db.backref('users', lazy='dynamic'))

    def is_active(self):
        """Return True if the user is active."""
        return self.active

    def get_urole(self):
        """Return urole index if the user is admin."""
        return self.urole

    def get_id(self):
        """Return the username to satisfy Flask-Login's requirements."""
        return self.username

    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return self.authenticated

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def verify_password(self, password):
        return bcrypt.verify(password, self.password)

    def is_game_owner(self, game):
        return game.users.first() == self

    def choose_card_for_game(self, game_id, card_id):
        hand = self.get_game_hand(game_id)
        if card_id == None:
            card = hand.cards.all().pop(random.randrange(len(hand.cards.count())))
        else:
            card = hand.cards.query().filter(card_id==card_id).first()
            hand.cards.all().remove(card)
        db.session.add(hand)
        chosen_card = ChosenCard(game_id=game_id, user_id=self.id,
            card_id=card_id)
        db.session.add(chosen_card)
        db.session.commit()
        return chosen_card

    def get_game_heap(self, game_id):
        return Heap.query.filter(user_id=self.id, game_id=game_id).first()

    def get_game_hand(self, game_id):
        return Hand.query.filter(user_id=self.id, game_id=game_id).first()

    def has_chosen_card(self, game_id):
        return ChosenCard.query.filter(user_id=self.id,
                game_id=game_id).count() == 1

    def get_chosen_card(self, game_id):
        return ChosenCard.query.filter(user_id=self.id,
                game_id=game_id).first()

    def serialize(self):
        return {
                'id': self.id,
                'username': self.username,
                'urole': self.urole
                }

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    cow_value = db.Column(db.Integer, nullable=False)

    def __init__(self, number, cow_value):
        self.number = number
        self.cow_value = cow_value

    def serialize(self):
        return {
                'id': self.id,
                'number': self.number,
                'cow_value': self.cow_value
                }

class Game(db.Model):
    STATUS_CREATED = 0
    STATUS_STARTED = 1
    STATUS_FINISHED = 2

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Integer, nullable=False, default=STATUS_CREATED)

    def get_lowest_value_column(self):
        column_value = 9000
        for column in self.columns:
            tmp_column_value = column.get_value()
            if tmp_column_value < column_value:
                lowest_value_column = column
        return lowest_value_column

    def get_suitable_column(self, chosen_card):
        diff = 104
        user_game_heap_changed = False
        for column in self.columns.all():
            last_card = columns.cards.order_by(model.Card.number.asc()).last()
            diff_temp = chosen_card.number - last_card.number
            if diff_temp > 0 and diff_temp < diff:
                diff = diff_temp
                chosen_column = column
        if diff == 104:
            if chosen_card.user.get_urole() == User.USER_ROLE_BOT:
                chosen_column = self.get_lowest_value_column()
                chosen_column.replace_by_card(chosen_card)
            else:
                raise NoSuitableColumnException(chosen_card.user_id)
        return chosen_column

    def resolve_turn(self):
        chosen_card = self.chosen_cards.join(cards,
                chosen_cards.card_id==cards.id).order_by(model.Card.number.asc()).first()
        if not chosen_card:
            return
        chosen_column = self.get_suitable_column(chosen_card)
        if chosen_column.cards.count() == 5:
            user_game_heap = user.get_game_heap(self.id)
            user_game_heap.cards.append(chosen_column.cards)
            db.session.add(user_game_heap)
            chosen_column.cards = []
            db.session.add(chosen_column)
            db.session.commit()
            user_game_heap_changed = True
        chosen_column.cards.append(chosen_cards.card)
        db.session.add(chosen_column)
        db.session.delete(chosen_card)
        db.session.commit()
        self.check_status()
        return chosen_column

    def setup_game(self):
        max_card_number = db.session.query(func.max(Card.number)).scalar()
        card_set = list(range(1,max_card_number + 1))
        for user in self.users.all():
            user_hand = Hand(user=user, game=self)
            for i in range(app.config['HAND_SIZE']):
                card_number = card_set.pop(random.randrange(len(card_set)))
                user_hand.cards.append(Card.query.filter(Card.number==card_number).first())
                db.session.add(user_hand)
        for i in range(app.config['BOARD_SIZE']):
            column = Column(game_id=self.id)
            card_number = card_set.pop(random.randrange(len(card_set)))
            column.cards.append(Card.query.filter(Card.number==card_number).first())
            db.session.add(column)
        db.session.commit()

    def get_results(self):
        result = {}
        for user in self.users.all():
            user_game_heap = user.get_game_heap(self.id)
            result[user.username] = user_game_heap.get_value()
        return results

    def check_status(self):
        if self.users.first().get_game_hand(self.id).cards.count() == 0:
            self.status = Game.FINISHED
            db.session.add(self)
            db.session.commit()

    def get_user(self, user_id):
        return self.users.query.filter(id=user_id).first()

    def serialize(self):
        return {
                'id': self.id,
                'users': self.users.all(),
                'status': self.status
                }

column_cards = db.Table('column_cards',
        db.Column('column_id', db.Integer, db.ForeignKey('column.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Column(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=column_cards,
            backref=db.backref('columns', lazy='dynamic'))

    def replace_by_card(self, chosen_card):
        user_game_heap = chosen_card.user.get_game_heap(chosen_card.game_id)
        user_game_heap.cards.appen(self.cards)
        db.session.add(user_game_heap)
        self.cards = chosen_card.card
        db.session.add(self)
        db.session.delete(chosen_card)
        db.session.commit()

    def get_value(self):
        return sum(card.cow_value for card in self.cards)

    def get_columns(self):
        return self.columns.all()

    def serialize(self):
        return {
                'id': self.id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

hand_cards = db.Table('hand_cards',
        db.Column('hand_id', db.Integer, db.ForeignKey('hand.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Hand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=hand_cards,
            backref=db.backref('hands', lazy='dynamic'))

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

heap_cards = db.Table('heap_cards',
        db.Column('heap_id', db.Integer, db.ForeignKey('heap.id')),
        db.Column('card_id', db.Integer, db.ForeignKey('card.id'))
)

class Heap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    cards = db.relationship('Card', secondary=heap_cards,
            backref=db.backref('heaps', lazy='dynamic'))

    def get_value(self):
        return sum(card.cow_value for card in self.cards)

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'cards': self.cards.all()
                }

class ChosenCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    card_id = db.Column(db.Integer, db.ForeignKey('card.id'))

    def serialize(self):
        return {
                'id': self.id,
                'user_id': self.user_id,
                'game_id': self.game_id,
                'card_id': self.card_id
                }
