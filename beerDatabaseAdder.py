import collections
import utils
import settings
import re
import heapq
import operator

from collections import defaultdict
import math
from stemming import porter2



from beer_average_rating import BeerAverage

def tokenize(text):
    """
    Take a string and split it into tokens on word boundaries.

    A token is defined to be one or more alphanumeric characters,
    underscores, or apostrophes.  Remove all other punctuation, whitespace, and
    empty tokens.  Do case-folding to make everything lowercase. This function
    should return a list of the tokens in the input string.
    """
    tokens = re.findall("[\w']+", text.lower())
    return [porter2.stem(token) for token in tokens]


class Search(object):
    """ A search engine for beers. """
    def __init__(self):
        """
        purpose: Create the search engine for beers
        parameters:
            mongo - the pymongo Database object

        """
        # index maps tokens to a set of ids containing that token
        self.index = defaultdict(set)
        # tweets maps tweet ids to tweet dictionaries
        self.beers = {}
        # term_idf map tokens to idf values
        self.term_idf = {}

    def index_beers(self,beers):
        """
        purpose: read the beer dicts and store them in the database
        preconditions: the database is empty
        parameters:
          beers - an iterator of beer dictionaries
        returns: none
        """
        print 'indexing'
        df = defaultdict(int)
        for beer in beers:
            id = beer['BeerId']
            self.beers[id] = beer
            # we make a set of the tokens to remove duplicates
            beer['tokens'] = tokenize(beer["Name"]+ ' '+beer["Brewery"])
            for token in set(beer['tokens']):
                self.index[token].add(id)
                df[token]+=1
        print 'tf-idfing'
        self.term_idf = {
            term:math.log(len(self.beers)/count,2)
            for term,count in df.iteritems()
            }

        # we have to have the term_idf to cal
        for beer in self.beers.itervalues():
            beer['vect'] = self._normed_vect(beer['tokens'])

    def _term_tf_idf(self, term, count):
        if count==0 or term not in self.term_idf:
            return 0
        return (1+math.log(count,2))*self.term_idf[term]

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


def main():
    db = utils.connect_db('Two_Pick_Too_Drunk')
    beer_collection = db['beer']
    beer_collection.remove()
    
    beer_rating = BeerAverage()

    print 'Loading Beers'
    beers = utils.read_beers()
    brewery = []
    beersCount = 0
    for beer in beers:
        beersCount +=1
        if beer['Brewery'] not in brewery:
            brewery.append(beer['Brewery'])
        
        if beer['BeerId'] in beer_rating:
            doc = {'Brewery'   : beer['Brewery'],
                   'BeerId'    : beer['BeerId'],
                   'Name'      : beer['Name'],
                   'BreweryId' : beer['BreweryId'],
                   'AverageRating': beer_rating[beer['BeerId']]
                  }
        else:
            doc = {'Brewery'   : beer['Brewery'],
                   'BeerId'    : beer['BeerId'],
                   'Name'      : beer['Name'],
                   'BreweryId' : beer['BreweryId']
                  }

        beer_collection.insert(doc)
    print str(beersCount) + ' Beers over ' + str(len(brewery)) + ' Brewerys'
    search = Search()
    beers = beer_collection.find()
    search.index_beers(beers)
    print 'inputing into DB'
    for beer in search.beers:
        beerData=  search.beers[beer]
        beer_collection.update({"BeerId":beerData['BeerId']},{"$set":{"tokens":beerData["tokens"],"vect":beerData["vect"]}})
    index = {}
    for x in search.index:
        index[x] = list(search.index[x])
    db['search'].remove({"SearchIndex":"Beer"})
    db['search'].insert({"SearchIndex":"Beer","Index":index,"termIdf":search.term_idf})    


    


if __name__=="__main__":
    main()
