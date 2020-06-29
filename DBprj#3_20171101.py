from konlpy.tag import Mecab
from pymongo import MongoClient
from itertools import combinations

stop_word = dict()
DBname = "db20171101"
conn = MongoClient("localhost")
db = conn[DBname]
db.authenticate(DBname, DBname)

def make_stop_word():
    f = open("wordList.txt", "r")
    while True:
        line = f.readline()
        if not line:
            break
        stop_word[line.strip()] = True
    f.close()

def p0():
    col1 = db['news']
    col2 = db['news_freq']
    
    col2.drop()

    for doc in col1.find():
        contentDic = dict()
        for key in doc.keys():
            if key != "_id":
                contentDic[key] = doc[key]
        col2.insert(contentDic)

def morphing(content):
    mecab = Mecab()
    morphList = []
    for word in mecab.nouns(content):
        if word not in stop_word:
            morphList.append(word)
    return morphList

def p1():
    for doc in db['news_freq'].find():
        doc['morph'] = morphing(doc['content'])
        db['news_freq'].update({"_id": doc['_id']}, doc)

def p2():
    #news morphs of db.news_freq.findOne()
    doc = db['news_freq'].find_one()
    for w in doc['morph']:
        print(w)

def p3():
    col1 = db['news_freq']
    col2 = db['news_wordset']
    col2.drop()
    for doc in col1.find():
        new_doc = dict()
        new_set = set()
        for w in doc['morph']:
            new_set.add(w)
        new_doc['word_set'] = list(new_set)
        new_doc['news_freq_id'] = doc['_id']
        col2.insert(new_doc)

def p4():
    #news wordset of db.news_wordset.findOne()
    doc = db['news_wordset'].find_one()
    for w in doc['word_set']:
        print(w)

def p5(length):
    """
    make frequent item_set
    and insert new collection (candidate_L+"length")
    """
    min_sup = (db['news'].count())*0.04
    
    #candidate_L1
    if length >= 1:
        candb = db['candidate_L1']
        candb.drop()
        dict1 = {}
        
        for doc in db['news_wordset'].find():
            for w in doc['word_set']:
                if w in dict1: 
                    dict1[w] = dict1[w] + 1
                else:
                    dict1[w] = 1

        for w, count in dict1.items():
            if (count < min_sup): continue
            word_doc = {}
            word_doc['item_set'] = [w]
            word_doc['support'] = count
            candb.insert(word_doc)
    
    #candidate_L2 or candidate_L3
    if length >= 2:
        dict2 = {}
        candb = db['candidate_L'+str(length)]
        candb.drop()
         
        for doc in db['news_wordset'].find():
            wordlist = []
            for w in doc['word_set']:
                if (dict1[w] > min_sup):
                    wordlist.append(w)
            comb = list(combinations(wordlist, length))
            
            for t in comb:
                t = frozenset(t)
                if t in dict2:
                    dict2[t] = dict2[t] + 1
                else:
                    dict2[t] = 1
        
        for wset, count in dict2.items():
            if (count < min_sup): continue
            word_doc = {}
            word_doc['item_set'] = list(wset)
            word_doc['support'] = count
            candb.insert(word_doc)
    
def p6(length):
    """
    make strong association rule
    and print all of strong rules
    by length-th frequent item set
    """
    min_conf = 0.8
    
    if length == 2:
        dic = {} 
        for doc in db['candidate_L2'].find():
            for w in doc['item_set']:
                if w in dic:
                    dic[w] += doc['support']
                else:
                    dic[w] = doc['support']

        for doc in db['candidate_L2'].find():
            for w in doc['item_set']:
                confidence = doc['support']/dic[w]

            if confidence >= min_conf:
                if w == doc['item_set'][0]:
                    s = "{0} => {1}\t{2}".format(w, doc['item_set'][1], confidence)
                else:
                    s = "{0} => {1}\t{2}".format(w, doc['item_set'][0], confidence)
                print(s)
        
    elif length == 3:
        dic = {}
        for doc in db['candidate_L3'].find():
            items = doc['item_set']
            sets = []
            sets.append(frozenset(items[0:1]))
            sets.append(frozenset(items[1:2]))
            sets.append(frozenset(items[2:3]))
            sets.append(frozenset(items[0:2]))
            sets.append(frozenset(items[1:3]))
            sets.append(frozenset(items[0:1])|frozenset(items[2:3]))

            for w in sets:
                if w in dic:
                    dic[w] += doc['support']
                else:
                    dic[w] = doc['support']
    
        for doc in db['candidate_L3'].find():
            items = doc['item_set']
            sets = []
            sets.append(frozenset(items[0:1]))
            sets.append(frozenset(items[1:2]))
            sets.append(frozenset(items[2:3]))
            sets.append(frozenset(items[0:2]))
            sets.append(frozenset(items[1:3]))
            sets.append(frozenset(items[0:1])|frozenset(items[2:3]))
            
            for w in sets:
                confidence = doc['support']/dic[w]
                if confidence >= min_conf:
                    l1 = list(w)
                    l2 = list(set(items)-w)
                    if len(w) == 1:
                        s = "{0} => {1}, {2}\t{3}".format(l1[0], l2[0], l2[1], confidence)
                    elif len(w) == 2:
                        s = "{0}, {1} => {2}\t{3}".format(l1[0], l1[1], l2[0], confidence)
                    print(s)

def printMenu():
    print("0. CopyData")
    print("1. Morph")
    print("2. print morphs")
    print("3. print wordset")
    print("4. frequent item set")
    print("5. association rule")
    
if __name__ == "__main__":
    make_stop_word()
    printMenu()
    selector = int(input())
    if selector == 0:
        p0()
    elif selector == 1:
        p1()
        p3()
    elif selector == 2:
        p2()
    elif selector == 3:
        p4()
    elif selector == 4:
        print("input length of the frequent item:")
        length = int(input())
        p5(length)
    elif selector == 5:
        print("input length of the frequent item:")
        length = int(input())
        p6(length)
