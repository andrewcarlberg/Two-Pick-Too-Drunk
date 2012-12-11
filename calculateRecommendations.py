import time
from recommender import Recommender
from datetime import datetime
import utils


class RecommendationCalculations():
    def __init__(self):
        db = utils.connect_db('Two_Pick_Too_Drunk')
        collection = db['user']
        last_update_start = datetime.today()
        reviews = 'reviewer'
        clusters = 'reviewer_cluster'
        updated = (False,1)
        recommenderer = Recommender()
        while 1:
            users  = collection.find({"last_beer_update":{"$gte":last_update_start}})
            start_time = time.time()
            for user in users:
                (results,result_set) = recommenderer.recommender(user["Beers_Rated"], reviews, clusters, db)
                collection.update({"_id": user["_id"]}, {"$set": {"Recommendations": results}})
                updated = (True,1)
            end_time = time.time()
            if updated[0]:
                print 'done with updation after %.3f seconds'%(end_time-start_time)

            last_update_start = datetime.now()
            if updated[0]:
                time.sleep(updated[1]*10);
                print 'Slept for '+str(updated[1]*10) + ' seconds'
                updated = (False,updated[1])
            else:
                if updated[1] < 30:
                    updated = (False,updated[1]+1)
                    time.sleep(updated[1]*10);
                    print 'Slept for '+str(updated[1]*10) + ' seconds'
                else:
                    time.sleep(updated[1]*10);
                    print 'Slept for '+str(updated[1]*10) + ' seconds'
                


def main():
    RecommendationCalculations()

if __name__=="__main__":
    main()
 
