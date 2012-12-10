Two-Pick-Too-Drunk
==================

CSCE 470 beer recommender service

##To Setup:
* start MongoDB
* run script RunMe
* In order to get reviews you must cluster either the O'bannons Reviews or all reviews
* Exports of each database collection are stored in Cached Database.  Importing them will allow you avoid using the RunMe.

##To Run
* Start MongoDB
* Run ./launch.py
* In another terminal run "python claculateRecommendations.py"
* go to localhost:6488
* On the first time running the website, go to /addObannons to add the places into the database.  Verison 2.0 will  make this easier.


