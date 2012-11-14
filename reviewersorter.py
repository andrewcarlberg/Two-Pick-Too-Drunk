import collections
import utils
import settings
import re


def main():
    db = utils.connect_db('msl', remove_existing=True)
    reviewer_collection = db['reviewer']
    
    reviews = utils.read_beers()

   
    count = 0
    count_unique = 0
    repeat = 0
    total_ratings = 0


    for review in reviews:
        
        temp_person = review['Reviewer']
        temp_dic = review
        
        
        if reviewer_collection.find_one({"reviewer" : temp_person}):
            doc = reviewer_collection.find_one({"reviewer" : temp_person})
            
            doc[temp_dic['BeerId']]=temp_dic['rating']
            
            reviewer_collection.update({"reviewer" : temp_person}, doc)
            total_ratings = float(temp_dic['rating']) + total_ratings
            repeat = repeat + 1
            
     
        else:
            count_unique = count_unique+1
            #temp_dic = review
            
            doc = {"reviewer": temp_person,
                    temp_dic['BeerId'] : temp_dic['rating']}
            reviewer_collection.insert(doc)
            total_ratings = float(temp_dic['rating']) + total_ratings

            
        count= count +1
      
        
   

    print "Total lines ", count
    print "Repeated reviewers ", repeat
    print "Number of reviewers ",count_unique
    print "Average rating ", total_ratings/count
    print
    """ makeing stats """

    # 1 rating so lengeth = 3
    few_ratings=0
    # 2-5 ratings so length 4 - 7
    some_ratings = 0
    # < 5 so greater than 7
    lots_ratings = 0
    
    
    cursor = reviewer_collection.find()
    for d in cursor:
        doc_length =len(d.keys())
        if doc_length == 3:
            few_ratings +=1
        elif doc_length < 8:
            some_ratings +=1
        else:
            lots_ratings +=1
            
    print "one rating", few_ratings
    print "2-5 ratings", some_ratings
    print " more than 5 ratings", lots_ratings
    
    

    
if __name__=="__main__":
    main()
