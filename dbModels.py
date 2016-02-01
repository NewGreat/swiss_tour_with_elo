__author__ = 'andre'
from andreutils import make_pw_hash, valid_pw
from google.appengine.ext import vendor
# Add any libraries installed in the "lib" folder.
vendor.add('libs')
import logging
from google.appengine.ext import db
from google.appengine.api import memcache
import main


class User(db.Model):
    name = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()

    @classmethod   #mean that this method is static and is called on class (ex: User.by_id)
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())
        #return db.GqlQuery("SELECT * FROM User WHERE __key__=uid")

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        #u = db.GqlQuery("SELECT * FROM User WHERE name = name")
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


def users_key(group = 'default'):
    return db.Key.from_path('users', group)


class Player(db.Model):
    name = db.StringProperty(required=True)
    rating = db.IntegerProperty(required=True)
    opponents = db.ListProperty(long)
    results = db.ListProperty(str)
    games = db.IntegerProperty()
    wins = db.IntegerProperty()
    loses = db.IntegerProperty()
    draws = db.IntegerProperty()


    def render(self):
        return main.render_str("player.html", player = self)

    def as_dict(self):
        time_fmt = '%c'
        results_for_touralgorithm = []
        for result in list(self.results):
            if result == "W":
                results_for_touralgorithm.append([1,0,0])
            if result == "L":
                results_for_touralgorithm.append([0,1,0])
            if result == "D":
                results_for_touralgorithm.append([0,0,1])
            if result == "B":
                results_for_touralgorithm.append([0,0,0])
        d = {'Name': self.name,
             'Opponents': self.opponents,
             'Results': results_for_touralgorithm,
             'Rating': self.rating,
             'Games': self.games,
             'Wins': self.wins,
             'Loses': self.loses,
             'Draws': self.draws,
        }
        return d

    def get_stat(self):
        self.games = self.wins = self.loses = self.draws = 0
        for results in list(self.results):
            self.games += 1
            self.wins += results[0]
            self.loses += results[1]
            self.draws += results[2]
        return self.games,self.wins, self.loses, self.draws


class RoundAndMatches(db.Model):
    number = db.IntegerProperty(required=True)
    is_finished = db.IntegerProperty(required=True, choices={0, 1})
    p1_ids = db.ListProperty(long)
    p2_ids = db.ListProperty(long)
    results = db.ListProperty(str)

    def render(self, user=None, players=list([])):
        if self.is_finished:
            winners = []
            for winner in list(self.results):
                if winner=="Player1":
                    winners.append([1,0,0])
                elif winner=="Player2":
                    winners.append([0,1,0])
                elif winner=="Draw":
                    winners.append([0,0,1])
        return main.render_str("round.html", number = self.number, matches=self.get_matches(), user = user, p1_ids=self.p1_ids, is_finished=self.is_finished)

    def as_dict(self):
        time_fmt = '%c'
        d = {'Number': self.number,
             'Is_finished': self.is_finished,
             'P1_ids': self.p1_ids,
             'P2_ids': self.p2_ids,
             'Results': self.results}
        return d

    def get_matches(self):
        matches = []
        for index in range(len(self.p1_ids)):
            winner = []
            if self.is_finished:
                result = self.results[index]
                if result=="Player1":
                    winner = [1,0,0]
                elif result=="Player2":
                    winner = [0,1,0]
                elif result=="Draw":
                    winner = [0,0,1]
            matches.append([get_players(self.p1_ids[index])[0].name, get_players(self.p2_ids[index])[0].name, self.p1_ids[index], winner])
        return matches

    def getPairings(self):
        pairings = {}
        for index in range(len(self.p1_ids)):
            pairings[index + 1] = [self.p1_ids[index], self.p2_ids[index]]
        return pairings


def get_players(key="top_rated_players", update=False):
    #db.delete(db.GqlQuery("select * from Player order by created desc limit 10"))
    #Sdb.delete(Player.get(0))
    entries = memcache.get(str(key))
    if not entries or update:
        logging.error("DB QUERY Player")
       # entries = db.GqlQuery("select * FROM Player ORDER BY rating desc", 50).get()
        if key=="top_rated_players":
            entries = Player.all().order('-rating')
            memcache.set("top_rated_players", entries)
        else:
            entries = [Player.get_by_id((int(key)))]
            memcache.set(str(key), entries)
    return entries


def get_rounds(update = False):
    entries = memcache.get("rounds")
    if not entries or update:
        logging.error("DB QUERY Rounds")
        entries = db.GqlQuery("select * from RoundAndMatches order by number asc")
        memcache.set("rounds", entries)
    return entries
