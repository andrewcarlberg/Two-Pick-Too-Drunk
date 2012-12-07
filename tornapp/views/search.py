import re
import tornado.web
from tornado.escape import json_encode, json_decode
from viewlib import route, BaseHandler, async_yield
import utils
from passlib.hash import sha256_crypt

from ..models import Beer 




@route("/search")
class SearchHandler(BaseHandler):

    def get(self):
        query  = self.get_argument("q","")
        if query:
            beers = Beer.search().limit(30)
            self.render("search.html", beers = beers)
        else:
            self.render("search.html", beers = None)


    def post(self):
        query = self.get_argument("query", "")
        self.redirect("/search?q="+tornado.escape.url_escape(query))

