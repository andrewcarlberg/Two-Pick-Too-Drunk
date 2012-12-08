import re
import tornado.web
from tornado.escape import json_encode, json_decode
from viewlib import route, BaseHandler, async_yield
import utils
from passlib.hash import sha256_crypt
import time
from recommender import Recommender
from ..models import Beer,User
from datetime import datetime



@route("/search")
class SearchHandler(BaseHandler):

    def get(self):
        query  = self.get_argument("q","")
        if query:
            user =  self.get_current_user()
            updatedDict = dict()
            for x in user.Beers_Rated:
                updatedDict[x['BeerId']]=x['Rating']

            beers = Beer.search().limit(30)
            self.render("search.html", beers = beers, updatedDict=updatedDict)
        else:
            self.render("search.html", beers = None)


    def post(self):
        query = self.get_argument("query", "")
        self.redirect("/search?q="+tornado.escape.url_escape(query))

@route("/ratings")
class RatingHandler(BaseHandler):
    def post(self):
        start_time = time.time()

        args =  self.request.arguments
        user =  self.get_current_user()
        updatedDict = dict()
        for x in user.Beers_Rated:
            updatedDict[x['BeerId']]=x['Rating']
        for review in args:
            if review in updatedDict:
                if args[review][0] != updatedDict[review]:
                    
                    user.Beers_Rated.remove({"BeerId":review,"Rating":updatedDict[review]})
                    user.Beers_Rated.append({"BeerId":review,"Rating":args[review][0]})
                    user.last_beer_update = datetime.now()
            else:
                user.Beers_Rated.append({"BeerId":review,"Rating":args[review][0]})
                user.last_beer_update = datetime.now()               
        user.save()
        end_time = time.time()
        #print 'done with updation after %.3f seconds'%(end_time-start_time)

    def get_Recommendations(self):
        start_time = time.time()
        print "starting"
        user= self.get_current_user()

        db = utils.connect_db('Two_Pick_Too_Drunk')

        reviews = 'reviewer'
        clusters = 'reviewer_cluster'

        recommenderer = Recommender()
        (results,result_set) = recommenderer.recommender(user.Beers_Rated, reviews, clusters, db)
        end_time = time.time()
        print 'done with updation after %.3f seconds'%(end_time-start_time)



