#!/usr/bin/env python
# script to test your pagerank algorithm

import unittest
import recommender
import utils

TEST_INPUT = [{"BeerId": "1062", "Rating": "2.0"},
    {"BeerId": "409", "Rating": "2.67"},
    {"BeerId": "1907", "Rating": "3.8"},
    {"BeerId": "23720", "Rating": "3.24"},
    {"BeerId": "1212", "Rating": "2.56"},
    {"BeerId": "2508", "Rating": "1.0"},
    {"BeerId": "862", "Rating": "3.9"},
    {"BeerId": "909", "Rating": "3.75"},
    {"BeerId": "754", "Rating": "2.5"},
    {"BeerId": "3434", "Rating": "1.8"},
    {"BeerId": "72941", "Rating": "4.0"},
    {"BeerId": "1946", "Rating": "3.0"},
    {"BeerId": "924", "Rating": "2.98"},
    {"BeerId": "3295", "Rating": "1.87"},
    {"BeerId": "45576", "Rating": "3.1"}]
    



class TestRecommender(unittest.TestCase):
    def setUp(self):
        self.rec = recommender.Recommender()
        db = utils.connect_db('Two_Pick_Too_Drunk')
        self.rec.recommender(TEST_INPUT, 'obannons_reviews', 'obannons_reviews_cluster', db)

    #def _assert_recommender(self, expected):
        

    """ testing to see if returning closest cluster to the user input """
    def test_one_closest(self):
        min_dist = self.rec.min_cluster_dist
        min_cluster = self.rec.min_cluster
        self.assertEqual( .392346404686098 ,min_dist)
        self.assertEqual( 10 ,min_cluster)

    """ found average for one of the beers, test compared to that number
        testing beerId 607, 21 reviews avg review 3.483809524"""
    def test_two_avg(self):
        avg = self.rec.beer_final_avg['607']
        self.assertEqual( 3.483809523809525 ,avg)
        
        

   

if __name__ == '__main__':
    unittest.main()
