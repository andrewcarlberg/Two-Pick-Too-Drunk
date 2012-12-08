#!/usr/bin/env python
from collections import defaultdict
import copy
import re
import time
import utils
import ujson
import math
import random
import sys

class ClusterAnalyer(object):
    def __init__(self):
        """
        Create the search engine for tweets

        This method should create two member variables: an index that will map
        tokens to tweets ids, and a container to store the actual tweets.

        In future homeworks, Expect this method to change a lot as you move from
        storing tweets in a memory to using a database.
        """
        # index maps tokens to a set of ids containing that token
        self.index = defaultdict(set)
        # tweets maps tweet ids to tweet dictionaries
        self.reviewers = {}
        # term_idf map tokens to idf values
        self.term_idf = {}

    def index_tweets(self,reviews):
        """
        purpose: read the tweet dicts and store them in your inverted index
        parameters:
          tweets - an iterator of tweet dictionaries
        returns: none
        """
        print 'Indexing'
        df = defaultdict(int)
        numberOfReivews = reviews.count()
        print numberOfReivews
        for review in reviews:
            user = review['reviewer']
            self.reviewers[user] = {'Ratings':review['Ratings']}

        print 'normalizing'
        for reviewer in self.reviewers.itervalues():
            reviewer['vect'] = self._normed_vect(reviewer['Ratings'])

    def cluster(self,reviews,db=None,collection=None):
        self.index_tweets(reviews)
        self.results = {'rss':1000000000000000}
        y=0
        while y<19:
            print 'Run number: ' + str(y+1)
            self.Centroids = self.setCentroids(int(math.sqrt(len(self.reviewers)/2)))
            x=1
            while 1:

                print 'Clustering...'
                print 'Round: '+str(x)
                self.find_cluster()
                self.ReassignCentroids()
                if self.AmIDone():
                    break
                self.Centroids = copy.deepcopy(self.newCentroids)
                del self.newCentroids
                del self.UserCentroidDict
                x+=1
            rss = 0
            for centroid in self.UserCentroidDict.keys():
                print 'Cluster: ' + str(centroid) + ' has ' + str(len(self.UserCentroidDict[centroid])) + ' users.'
                rss+=self.RSS(self.UserCentroidDict[centroid],self.Centroids[centroid])
            print 'rss: '+str(rss) 
            if rss < self.results['rss']:
                self.results['rss']=rss
                self.results['cluster'] = copy.deepcopy(self.UserCentroidDict)
            y+=1
        if db and collection:
            self._Print_and_Save_Results(db,collection)
        

    def _Print_and_Save_Results(self,db,collection):
        print '\n\n\n\nResults:'
        print self.results
        cluster_collection = db[collection+'_cluster']
        cluster_collection.remove()
        for cluster in self.results['cluster']:
            cluster_collection.insert({'Cluster':cluster,
                                       'Reviewers':self.results['cluster'][cluster],
                                       'Centroid':self.Centroids[cluster]})

    def find_cluster(self):
        print 'Assisgning Cluster'
        self.UserCentroidDict = dict()
        for reviewer in self.reviewers:
            minDist = (100000,-1) #way to large
            for centroid in self.Centroids:
                dist = self.CalcDistance(self.reviewers[reviewer]['vect'],centroid)
                if dist<minDist[0]:
                     minDist = (dist,self.Centroids.index(centroid))
            if minDist[1] not in self.UserCentroidDict:
                self.UserCentroidDict[minDist[1]]=[reviewer]
            else:
                self.UserCentroidDict[minDist[1]].append(reviewer)
            


    def RSS(self,userlist,dict1):
        RSS = 0
        for user in userlist:
            RSS += self.CalcDistance(self.reviewers[user]['vect'],dict1)
        return RSS

    def AmIDone(self):
        for centroids in self.Centroids:
            dist = self.CalcDistance(centroids,self.newCentroids[self.Centroids.index(centroids)])
            if dist > 1e-6:
                return False
        return True

    def ReassignCentroids(self):
        print 'Recalculating Centroids'
        self.newCentroids = copy.deepcopy(self.Centroids)
        for centroid in self.UserCentroidDict.keys(): 
            CentVect = self.newCentroids[centroid]
            for user in self.UserCentroidDict[centroid]:
                for token in self.reviewers[user]['vect']:
                    if type(CentVect[token]) is not list:
                        CentVect[token] = [self.reviewers[user]['vect'][token]]
                    else:
                        CentVect[token].append(self.reviewers[user]['vect'][token])                  
            for token in CentVect.keys():
                if type(CentVect[token]) is not float:
                    CentVect[token] = sum(CentVect[token])/len(CentVect[token])
            
    def CalcDistance(self, dict1, dict2):
        distance = 0
        for token in dict1:
            distance += math.pow(dict1[token]-dict2[token],2)
        return math.sqrt(distance)

    def setCentroids(self,k):
        print 'Intializeing Centroids'
        print str(k) + ' Clusters will be created'
        x=0
        CentroidsList = []
        db = utils.connect_db('Two_Pick_Too_Drunk')
        bc = db['beer']
        beers = list()
        for y in bc.find():
            beers.append(y['BeerId'])
        while x<k:
            centroid = {}
            for token in beers:
                centroid[token]=random.random()
            CentroidsList.append(centroid)
            x+=1
        return CentroidsList

    def _normed_vect(self, tokens):
        """ take a list of tokens and convert it to a normalized tf-idf vector"""
        totalLength = 0
        for token in tokens:
            totalLength+= math.pow(float(token['Rating']),2)
        totalLength = math.sqrt(totalLength)

        vect = {}
        for token in tokens:
            vect[token['BeerId']] = float(token['Rating'])/totalLength
        return vect


def main():
    """
    Clustering!  Takes in agrument from commandline to with reviewer collection you want 
    to use to cluster.  Pretty much your choices are 'reviewer' or 'obannons_reviews'.

    Clustering will then take place and the results stored in the data base in either
    'reviewer_clusters' or 'obannons_reviews_cluster' with each cluster having a list 
    of users in the cluster
    """
    db = utils.connect_db('Two_Pick_Too_Drunk')
    reviewer_collection = db[sys.argv[1]]
    reviews = reviewer_collection.find()
    cluster = ClusterAnalyer()
    cluster.cluster(reviews,db,sys.argv[1])


if __name__=="__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print 'done with clustering after %.3f seconds'%(end_time-start_time)
