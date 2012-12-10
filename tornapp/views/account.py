import re
import tornado.web
from tornado.escape import json_encode, json_decode
from viewlib import route, BaseHandler, async_yield
import utils
from passlib.hash import sha256_crypt
from operator import itemgetter


from ..models import User,Beer




@route("/account/login")
class LoginHandler(BaseHandler):

  def get(self):
    self.render("account/login.html", next=self.get_argument("next","/"), message=self.get_argument("error","") )

  def post(self):
    nick = self.get_argument("email", "")
    password = self.get_argument("password", "")
    db = utils.connect_db('Two_Pick_Too_Drunk')
            
    p_hash =sha256_crypt.encrypt(password)
    u = User.search(nick_l=nick.lower()).first()
    print u
    if u:
        self.set_current_user(u)
        self.redirect("/account/home")

    else:
        error_msg = tornado.escape.url_escape("Wrong information")
        self.redirect("/account/login?error="+error_msg)


              
    

@route("/account/register")
class RegisterHandler(LoginHandler):

  def get(self):
    error = self.get_argument("error", "")    
    self.render(  "account/register.html", next=self.get_argument("next","/"), error=error)

  def post(self):
    args = self.request.arguments    
    print args
    db = utils.connect_db('Two_Pick_Too_Drunk')
    collection = db['User']
    u = User.search(nick_l=args['username'][0].lower()).first()
    print u
    if u:
        error_msg = u"?error=" + tornado.escape.url_escape("Login name already taken")
        self.redirect(u"/account/register" + error_msg)
    else:
        user = User(
                    nick = args['username'][0],
                    nick_l = args['username'][0].lower(),
                    email = args['email'][0],
                    password = sha256_crypt.encrypt(args['password'][0]),
                    name = args['fName'][0].strip() + ' ' + args['lName'][0].strip()
            )

        user.save()
        self.set_current_user(user)

        self.redirect("/account/home")

@route("/account/home")
class AccountHome(BaseHandler):

  def get(self):
    self.render("account/home.html")
    

@route("/account/logout")
class Logout(BaseHandler):
    def get(self):
        self.clear_current_user()
        self.redirect("/")

@route('/account/recommendations')
class HomePageHandler(BaseHandler):

    def get(self):
        user = self.get_current_user()
        recommendations = sorted(user.Recommendations.items(), key=itemgetter(1), reverse=True)
        top5 = recommendations[:5]
        bottom5 = recommendations[-5:]
        bottom5.reverse()
        beers = list()
        for x in top5+bottom5:
            beers.append(x[0])
        beerObjects = Beer.find({"BeerId":{"$in":beers}})
        
        lookUpBeer = dict()
        for x in beerObjects:
            lookUpBeer[x.BeerId] = {"name":x.Name,"brewery":x.Brewery,"avg":x.AverageRating}

        self.render("account/recommendations.html",top5=top5,bottom5=bottom5,lookUp = lookUpBeer)
        

@route('/account/ratings')        
class RatedHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        ratedDict = dict()
        for x in user.Beers_Rated:
            ratedDict[x['BeerId']]={"rating":x['Rating']}

        beersObjects = Beer.find({"BeerId":{"$in":ratedDict.keys()}})
        for beer in beersObjects:
            data = ratedDict[beer["BeerId"]]
            data["name"]=beer["Name"]
            data["brewery"]=beer["Brewery"]
            data["avg"] = beer["AverageRating"]
            ratedDict[beer["BeerId"]]=data
        self.render("account/rated.html", ratedDict=ratedDict)

