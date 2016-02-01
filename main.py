import os
import json, webapp2, jinja2
from dbModels import *
from andreutils import make_secure_val, check_secure_val, valid
import logging, time
from SwissTournament import  Tournament
from google.appengine.api import memcache
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=False)
#logging.getLogger().setLevel(logging.DEBUG)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)


class MainHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.write(json_txt)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'


class SignupHandler(MainHandler):
    def get(self):
        #self.response.headers['Content-Type'] = 'text/plain'
        self.render("signup.html")

    def post(self):
        self.uname = self.request.get('username')
        self.passw = self.request.get('password')
        self.vpassw = self.request.get('verify')
        self.email = self.request.get('email')


        have_error = False
        params = dict(username = self.uname, email = self.email)

        if not valid(self.uname, "username"):
            params['unameerror'] = "That's not a valid username."
            have_error = False
        if not valid(self.passw, "password"):
            params['passerror'] = "That's not a valid password."
            have_error = False
        if self.passw != self.vpassw:
            params['vpasserror'] = "Your passwords didn't match."
            have_error = False
        if not valid(self.email, "email"):
            params['emailerror'] = "That's not a valid email email."
            have_error = False

        if have_error:
            self.render("signup.html", **params)
        else:
            u = User.by_name(self.uname)
            if u:
                msg = 'That user already exists.'
                self.render('signup.html', unameerror = msg)
            else:
                u = User.register(self.uname, self.passw, self.email) # creates a new user
                u.put() # add him to database
                self.login(u) # set_cookie is called inside here to create the cookie
                self.redirect("/tournament")


class LoginHandler(MainHandler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/tournament')
        else:
            msg = 'Invalid login'
            self.render('login.html', error = msg)


class LogoutHandler(MainHandler):
    def get(self):
        self.logout()
        self.redirect('/tournament')

class TournamentHandler(MainHandler):


    def get(self):
        players = get_players()
        rounds = get_rounds()
        if self.format == 'html':
            last = RoundAndMatches.all().order('-number').get()
            state = 0
            if last:
                state = 1
            self.render('tournament.html', players=players, rounds=rounds, user = self.user, state = state)
        # else:
        #     return self.render_json([e.as_dict() for e in entries])

    def post(self):
        new_tournament_button = self.request.get("new_tour_button")
        add_player_button = self.request.get("add_player_button")
        next_round_button = self.request.get("next_round_button")
        next_round_button1 = self.request.get("next_round_button1")

        if new_tournament_button:
            checkbox_val = self.request.get("rem_pl_checkbox")
            db.delete(RoundAndMatches.all())
            # update cache by forcing query with memcache update
            get_rounds(True)
            players = get_players()
            if checkbox_val == "yes":
                db.delete(players)
            else:
                # Clear oponents and results, keep rating and name
                for player in players:
                    player.opponents = []
                    player.results = []
                    player.wins = player.loses = player.draws = player.games = 0
                    p = player.put()
                # update memcache for top_rated_players query
            memcache.flush_all()
            self.redirect("/tournament")

        if add_player_button:
            player_rating_editText = self.request.get("player_rating_editText")
            player_name_editText = self.request.get("player_name_editText")
            error = None
            if not player_name_editText:
                error = "Name not given!"
            elif not unicode(player_rating_editText).isnumeric() or int(player_rating_editText) < 1000 or int(player_rating_editText) > 3000:
                error = "Rating should be grater than 1000(beginner) and lower than 3000(supermaster)!"
            if error:
                self.render('tournament.html',players=get_players(), error=error, user=self.user)
            else:
                new_player = Player(name=player_name_editText, rating=int(player_rating_editText), opponents=[], results=[], wins=0, loses=0, draws=0, games=0)
                a_key = new_player.put()
                time.sleep(1)
                # update memcahce
                get_players("top_rated_players", True)
                get_players(a_key.id(), True)
                self.redirect("/tournament")

        if next_round_button:
            players = get_players()
            playersDict = self.constructPlayersDict(players)
            if players:
                tour = Tournament(playersDict)
                nextRound = tour.pairRound()
                # updated Players database with new opponents
                self.updatePlayerOpponentsDB(nextRound)
                # update RoundAndMatches database with new games
                self.updateRoundGamesDB(nextRound, 1)
            self.redirect("/tournament")

        if next_round_button1:
            lastround = RoundAndMatches.all().order('-number').get()
            resultlist = []
            error1 = None
            for player in lastround.p1_ids:
                checkbox_val = self.request.get(str(player))
                if checkbox_val:
                    resultlist.append(checkbox_val)
                else:
                    error1 = "You need to score all matches!"

                    break
            if error1:
                self.render('tournament.html', players=get_players(), rounds=get_rounds(), user=self.user, state=1, error1=error1)
            else:
                players = get_players()
                playersDict = self.constructPlayersDict(players)
                to = Tournament(playersDict)
                to.report_all(lastround.getPairings(), resultlist)
                # Update Player results in db
                pd = self.updatePlayersResultsDB(to.playersDict)
                # Update RounAndMatchesDB with results
                self.updateRoundResultsDB(resultlist, lastround)

                newPlayersDict = self.constructPlayersDict(get_players())
                tour = Tournament(newPlayersDict)
                nextRound = tour.pairRound()
                # updated Players database with new opponents
                self.updatePlayerOpponentsDB(nextRound)
                # update RoundAndMatches database
                self.updateRoundGamesDB(nextRound, lastround.number + 1)
                self.redirect("/tournament")


    def constructPlayersDict(self, players1):
        playersDict = {}
        for player in players1:
            playersDict[player.key().id()]  = player.as_dict()
        return playersDict

    def updatePlayerOpponentsDB(self, nextRound):
        players = get_players()
        plids = [player.key().id() for player in players]
        for p1_id, p2_id in nextRound.values():
            player1 = get_players(p1_id)[0]
            player1.opponents.append(p2_id)
            player1.put()
            plids.remove(player1.key().id())
            player2 = get_players(p2_id)[0]
            player2.opponents.append(p1_id)
            player2.put()
            plids.remove(player2.key().id())
            # update memcache
            get_players(p2_id, True)
            get_players(p1_id, True)
        for playerid in plids:
            player = get_players(playerid)[0]
            player.opponents.append(0)
            player.put()
            # update memcache
            get_players(player.key().id(), True )
        time.sleep(1)
        get_players("top_rated_players", True)

    def updatePlayersResultsDB(self, playersDict):
        for playerID in playersDict:
            result = []
            wins = loses = draws = games = 0
            if len(playersDict[playerID]["Results"]) < len(playersDict[playerID]["Opponents"]):
                result = "B"
            elif len(playersDict[playerID]["Results"]) == len(playersDict[playerID]["Opponents"]) :
                lastresult = playersDict[playerID]["Results"].pop()
                games = 1
                if lastresult[0] == 1:
                    wins = 1
                    result = "W"
                elif lastresult[1] == 1:
                    loses = 1
                    result = "L"
                elif lastresult[2] == 1:
                    draws = 1
                    result = "D"
            player = get_players(playerID)[0]
            player.wins += wins
            player.loses += loses
            player.draws += draws
            player.games += games
            if len(result) > 0:
                player.results.append(result)
            player.rating = playersDict[playerID]["Rating"]
            player.put()
            get_players(playerID, True)
        time.sleep(1)
        get_players("top_rated_players", True)

    def updateRoundGamesDB(self, nextRound, number):
        p1_ids = []
        p2_ids = []
        for match in nextRound:
            p1_ids.append(nextRound[match][0])
            p2_ids.append(nextRound[match][1])
        nextMatches = RoundAndMatches(number=number, is_finished=0, p1_ids=p1_ids, p2_ids=p2_ids)
        a_key = nextMatches.put()
        time.sleep(1)
        get_rounds(True)

    def updateRoundResultsDB(self, resultlist, round):
        round.results = resultlist
        round.is_finished = 1
        a_key =round.put()
        time.sleep(1)
        get_rounds(True)


class FlashHandler(MainHandler):
    def get(self):
        db.delete(RoundAndMatches.all())
        db.delete(Player.all())
        memcache.flush_all()
        self.redirect('/tournament')


app = webapp2.WSGIApplication([('/tournament/signup', SignupHandler),
                               ('/tournament/?(?:.json)?', TournamentHandler),
                               ('/tournament/login', LoginHandler),
                               ('/tournament/logout', LogoutHandler),
                               ('/tournament/flush', FlashHandler)], debug=True)


