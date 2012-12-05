import ujson
import unicodedata
import utils 
from reviewersorter import review_sorter
from ObannonsBeerList import OBD


def BeerAverage():
    db = utils.connect_db('Two_Pick_Too_Drunk')

    reviews = db['reviewer'].find()
    print 'Sorting reviewers'
    beer_ratings=dict()

    for review in reviews:
        for beer in review['Ratings']:
            if beer['BeerId'] in beer_ratings:
                beer_ratings[beer['BeerId']].append(float(beer['Rating']))
            else:
                beer_ratings[beer['BeerId']] = [float(beer['Rating'])]
        
    print 'Averaging Beers'

    for beer in beer_ratings:
        if len(beer_ratings[beer]) > 10:
            beer_ratings[beer] = sum(beer_ratings[beer])/float(len(beer_ratings[beer]))
        else:
            beer_ratings[beer]=-1
    return beer_ratings


if __name__=="__main__":
    main()
