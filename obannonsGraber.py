import ujson
import unicodedata
import utils 
from reviewersorter import review_sorter
from ObannonsBeerList import OBD


def main():
    db = utils.connect_db('Two_Pick_Too_Drunk')
    beer_collection = db['beers']

    ObannonsBeerList = OBD.keys()
    
    print 'Sorting Obannon\'s reviews'
    reviews = utils.read_beers()
    obannonsReviews = list()
    obannonsDict = dict()
    json = open('Reviews/ObannonsData.json','w')
    for review in reviews:
        if review['BeerId'] in ObannonsBeerList:
            obannonsReviews.append(review)
            s = ujson.dumps(review)
            json.write(s+'\n')
    json.close()
    reviewersorter = review_sorter('obannons_reviews')
    reviewersorter.sort_reviews(obannonsReviews)

    for review in obannonsReviews:
        if review['BeerId'] in obannonsDict:
            obannonsDict[review['BeerId']].append(review['Reviewer'])
        else:
            obannonsDict[review['BeerId']] = [review['Reviewer']]

    print 'Reveiews per Obannons Beers'
    for beer in obannonsDict:
        Beer = beer_collection.find_one({"BeerId":beer})
        print 'Beer: '+Beer['Brewery']+ ' '+ Beer['Name'] + '\nNumber of reviews: '+str(len(obannonsDict[beer]))+'\n'
    


if __name__=="__main__":
    main()
