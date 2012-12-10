import re
from copy import deepcopy
from datetime import datetime, timedelta
from json import JSONEncoder, loads
from random import randint
import re

from urllib import urlencode
from uuid import uuid4

import gridfs

from mogo import Model, Field, ReferenceField, ASC, DESC
from mogo.model import ObjectId
from mogo.connection import Connection as mogo_connection
from operator import itemgetter
from pymongo import DESCENDING,ASCENDING
from pymongo.errors import OperationFailure

from stemming.porter import stem
from settings import torn_settings as settings
from tornado.escape import xhtml_escape



now = datetime.now
_mentions_re = re.compile(r'(?<!\S)@((?![\d:]+(?:[pa]m)?\b)\w+)', re.I)


class ModelEncoder(JSONEncoder):
    """
    A generic Model encoder that will hopefully get the results of a
    model's _d() dictionary as input.
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, ReferenceField):
            return [str(type(obj)), obj.value_type, obj.mro]
        return JSONEncoder.default(self, obj)


class GPModel(Model):
    """
    Base class for all GivePath models that defines _d() so that models
    can be serialized, say to a JSON format. There is a recursionlimit
    parameter to limit the number of Reference
    """
    def _d(self, recursionlimit=2):
        """
        Build a dict from all non-callable entities attached to our object.
        """
        d = dict()
        for (k,v) in self.__dict__.iteritems():
            if not callable(v):
                prop = getattr(type(self),k,None)
                if prop:
                    if isinstance(prop, ReferenceField):
                        v2 = getattr(self, k)
                        for f in [v, v2]:
                            if isinstance(f, GPModel):
                                # limit depth of references we serialize
                                if recursionlimit > 0:
                                    recursionlimit -= 1
                                    d[k] = f._d(recursionlimit)
                                else:
                                    d[k] = (f._id)
                    else:
                        # otherwise, just put the value ...
                        t=(bool,basestring,int,long,float,list,dict,tuple,set)
                        if isinstance(v,t):
                            d[k] = v
        return d

    def _json(self, recursionlimit=10):
        " Returns a json representation of the dict from _d() "
        return ModelEncoder().encode(self._d(recursionlimit))


class User(GPModel):
    """
    Our definition of a system user.
    """
    name = Field()
    nick = Field()
    nick_l = Field()
    password = Field()
    email = Field()
    created_at = Field(default=now)
    last_login = Field(datetime, default=now)
    Beers_Rated = Field(list, default=[])
    To_Drink_Beers = Field(list, default=[])
    Recommendations = Field(dict, default={})
    last_beer_update = Field(datetime,default=now)

    @classmethod
    def lookup(cls, query, page=0, limit=5):
        db = mogo_connection.instance().get_database()
        qterms = [ t.lower().strip() for t in query.split() ]
        skip = limit * page
        retrieve_size = 80 # may need to be tuned
        intermediate = {}

        r = '|'.join([ "%s" % re.escape(r) for r in qterms ])
        regx = re.compile(r,re.IGNORECASE)
        q_lc = [ q.lower() for q in qterms ]
        users = User.find({
                '$or':[
                    {'name': {'$regex': regx}},
                    {'nick_l': {'$in': q_lc}}
                    ]
            }).sort([['nick_l', ASCENDING]]).limit(int(retrieve_size))


        ret_ = []
        for u in users:
            ret_.append(u)


        numpages = len(ret_)/float(limit)
        ret_ = ret_[skip: skip+limit]

        retvals = []
        for u in ret_:
            retvals.append({
                'nk': u.nick_l,
                'nm': u.long_name,
                'av': u.avatar_url(),
                })

        return retvals, numpages


class Beer(GPModel):
    """
    Beer!
    """
    Brewery = Field()
    BeerId = Field()
    Name = Field()
    BreweryId = Field()
    AverageRating = Field(default=-1)
    tokens = Field()
    vect = Field()
    sim = Field(default = 0)
    

class Pub(GPModel):
    """
    A Place

    TODO: Figure out how to enter this data.  Can be done later
    """
    name = Field()
    street = Field()
    city = Field()
    state = Field()
    phoneNumber = Field(int)
    zipCode = Field(int)
    beerList = Field(list)
    
