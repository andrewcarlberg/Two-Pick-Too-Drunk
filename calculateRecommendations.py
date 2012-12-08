import time
from recommender import Recommender
from datetime import datetime
import utils


class RecommendationCalculations():
    def __init__(self):
        db = utils.connect_db('Two_Pick_Too_Drunk')
        collection = db['user']
        last_update_start = datetime(2012, 12, 6)
        reviews = 'reviewer'
        clusters = 'reviewer_cluster'

        recommenderer = Recommender()
        while 1:
            users  = collection.find({"last_beer_update":{"$gte":last_update_start}})
            start_time = time.time()
            for user in users:
                (results,result_set) = recommenderer.recommender(user["Beers_Rated"], reviews, clusters, db)
                collection.update({"_id": user["_id"]}, {"$set": {"Recommendations": results}})
            end_time = time.time()
            print 'done with updation after %.3f seconds'%(end_time-start_time)

            last_update_start = datetime.now()
            time.sleep(10)


def main():
    RecommendationCalculations()

if __name__=="__main__":
    main()
 
