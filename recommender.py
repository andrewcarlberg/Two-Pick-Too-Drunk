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


class Recommender(object):
        
    def recommender(self, user_ratings, reviews, clusters, db):

        """ finding centroid/vector for user's rating """
        self.users = []
        self.only_users = []
        df = defaultdict(int)
        for thing in user_ratings:
            self.users.append(thing)
            self.only_users.append(thing['BeerId'])
        self.only_users = set(self.only_users)

        user_vector = self._normed_vect(self.users)

        """ finding the clusters from cluster.py """
        centroids_collection = db[clusters]
        reveiwer_centroids = centroids_collection.find()
        centers = []
        
        for c in reveiwer_centroids:
            centers.append(c['Centroid'])
     
        """ Finding the closest centroid to the user """

        min_cluster_dist = 100000
        min_cluster = 500
        current_cluster = 0

        for cluster in centers:
            dist = self.CalcDistance(user_vector, cluster)
            if dist<min_cluster_dist:
                min_cluster_dist = dist
                min_cluster = current_cluster
            current_cluster +=1

        print min_cluster

        """ For all reviews of beer in the cluster, find its average rating """
        reviewers_collection = db[clusters]
        reveiwer_list = reviewers_collection.find()
        reviewers = []

        count = 0
        for r in reveiwer_list:
            if count == min_cluster:
                reviewers = r['Reviewers']
            count += 1
    
        self.beer_avg = defaultdict(list)
        rating_collection = db[reviews]
        rating_list = rating_collection.find()
        
        for reviewer_info in rating_list:
            if reviewer_info['reviewer'] in reviewers:
                temp_list = reviewer_info['Ratings']
                for rating in temp_list:
                    temp_rating = rating['Rating']
                    self.beer_avg[rating['BeerId']].append(temp_rating)
      
        beer_reccomend = {}

        for beer in self.beer_avg:
            total = 0.0
            
            for x in self.beer_avg[beer]:   
                total = total + float(x)
            avg = total/len(self.beer_avg[beer])
            beer_reccomend[beer] = avg

        """ sort the average ratings,
        highest rating will be first recommendation it the user """

            
        beer_reccomend = sorted(beer_reccomend,key =beer_reccomend.get, reverse = True)
    
        #print beer_reccomend, "\n"
        beer_reccomend_set= set(beer_reccomend)
        beer_reccomend_set.difference_update(self.only_users)         
        #print beer_reccomend_set, "\n"

        """ prints best beer id """
        count = 0
        best_beer = 0
        for beer in beer_reccomend:
            if beer in beer_reccomend_set:
                best_beer = beer_reccomend[count]
                print "Most reccomended beer ", beer_reccomend[count]
                break
            count +=1

        """ finding more info about are best beer """
        beers_collection = db['beers']
        beers_list = beers_collection.find()

        for thing in beers_list:
            if thing['BeerId'] == best_beer:
                print "\t Beer: ",thing['Name']
                print "\t From: ",thing['Brewery'] 
                break


        
       
    def CalcDistance(self, dict1, dict2):
        distance = 0
        for token in dict1:
            distance += math.pow(dict1[token]-dict2[token],2)
        return math.sqrt(distance)


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
    Takes agrument from commandline, of json file that contains user's beer ratings
    """

    user_ratings = utils.read_beers()
    db = utils.connect_db('Two_Pick_Too_Drunk')

    reviews = 'obannons_reviews'
    clusters = 'obannons_reviews_cluster'

    recommenderer = Recommender()
    recommenderer.recommender(user_ratings, reviews, clusters, db)
    


if __name__=="__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print 'done with recommendation after %.3f seconds'%(end_time-start_time)

