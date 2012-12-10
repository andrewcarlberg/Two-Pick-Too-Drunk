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
from stemming import porter2
import heapq
import operator
import math
from collections import defaultdict




@route("/search")
class SearchHandler(BaseHandler):

    def get(self):
        query  = self.get_argument("q","")
        user = self.get_current_user()
        if query:
            updatedDict = {}
            for x in user.Beers_Rated:
                updatedDict[x['BeerId']]=x['Rating']
            results = self.search_results(query)
            self.render("search.html", beers = results, updatedDict=updatedDict)
        else:
            self.render("search.html", beers = None)
    
    def search_results(self, query):
        db = utils.connect_db('Two_Pick_Too_Drunk')
        tokens = self.tokenize(query)
        index = db['search'].find_one({"SearchIndex":"Beer"})['Index']
        self.term_idf = db['search'].find_one({"SearchIndex":"Beer"})['termIdf']
            
        id_sets = list()
        for token in tokens:
            if token in index:
                id_sets += index[token]
        id_sets = set(id_sets)
        ids = list(id_sets)
        if not id_sets or not all(id_sets):
            return []
        beers = Beer.find({"BeerId":{"$in":ids}})
        beerReturn = list()
        for x in beers:
            beerReturn.append({
                "Name":x.Name,
                "BeerId":x.BeerId,
                "Brewery":x.Brewery,
                "AverageRating":x.AverageRating,
                "vect":x.vect,
                "tokens":x.tokens})
        query_vect = self._normed_vect(tokens)
        for beer in beerReturn:
            beer['sim'] = sum(
                    query_vect[k]*beer['vect'].get(k,0)
                    for k in query_vect
                    )

        return heapq.nlargest(20, beerReturn, key=operator.itemgetter('sim'))

    def _normed_vect(self, tokens):
        """ take a list of tokens and convert it to a normalized tf-idf vector"""
        counts = defaultdict(int)
        for token in tokens:
            counts[token]+=1
        vect = {
                term:self._term_tf_idf(term,count)
                for term,count in counts.iteritems()
                }
        mag = math.sqrt(sum(x**2 for x in vect.itervalues()))
        return {term:weight/mag for term,weight in vect.iteritems()}

    def _term_tf_idf(self, term, count):
        if count==0 or term not in self.term_idf:
            return 0
        return (1+math.log(count,2))*self.term_idf[term]


    def tokenize(self,text):
        """
        Take a string and split it into tokens on word boundaries.

        A token is defined to be one or more alphanumeric characters,
        underscores, or apostrophes.  Remove all other punctuation, whitespace, and
        empty tokens.  Do case-folding to make everything lowercase. This function
        should return a list of the tokens in the input string.
        """
        tokens = re.findall("[\w']+", text.lower())
        return [porter2.stem(token) for token in tokens]


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
                    if args[review][0] == "0":
                        print review
                        user.Beers_Rated.remove({"BeerId":review,"Rating":updatedDict[review]}) 
                    else:
                        user.Beers_Rated.remove({"BeerId":review,"Rating":updatedDict[review]})
                        user.Beers_Rated.append({"BeerId":review,"Rating":args[review][0]})
                    user.last_beer_update = datetime.now()
            else:
                if args[review][0] != "0":
                    user.Beers_Rated.append({"BeerId":review,"Rating":args[review][0]})
                    user.last_beer_update = datetime.now()               
        user.save()
        end_time = time.time()
        #print 'done with updation after %.3f seconds'%(end_time-start_time)

