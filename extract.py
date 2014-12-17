#!/usr/bin/python2.7
# extract.py
# Jeremy Johnston

"""
Given the  rank result output, summarize the best document.

"""

from __future__ import division 
import sys
import getopt
import os
import math
from collections import deque
import time
import logging
import rank
from rank import readModel
from genModel import Unigram, Bigram, FeatureSet

logging.basicConfig(filename="extract.log", level=logging.DEBUG)

class Results():
    def __init__(self):
        self.query = []
        self.p = 0.0
        self.baseP = 0.0
        self.pDiff = 0.0 
        self.originFile = ""
        self.modelFile = ""
        self.model = ""
        self.colFile = ""
        self.colModel = ""
        self.sentences = []
        self.summary = ""
        self.rank = 1000
        self.summaryCentrality = 0 
        

def summarize(sentences, model, colModel):
    """ Summarize a listing of sentences by choosing most central sentence.
    
        Given a model over a set of sentences, and a collective model over the set of documents
        including the document containing those sentences, compute centrality of each sentence 
        using tf_idf_cosine().
        
        The top few sentences with the greatest centrality is then used as the summary.
        
        centrality(x) = (1/K) * SUM[all y](tf_idf_cosine(x,y))
        where x and y are sentences in document.
        
        Refer to p792 J&M 
    """
    
    print 'Finding centralities over {0} sentences...'.format(len(sentences))
    
    # First fetch idf of each term in colModel, the count of the term
    print '\t...computing idf values...'
    idf = {} 
    for unigram in colModel.words.itervalues():
        idf[unigram.word] = unigram.count
        
    # Fetch term frequencies; the number of bigrams here 
    print '\t...computing tf values...'
    tf = {} 
    for unigram in model.words.itervalues(): 
        tf[unigram.word] = len(unigram.bigrams) 
        
    K = len(sentences) 
    
    # Find centrality values 
    centralities = {}
    bestC = 0 
    for s in sentences:
        centralities[s] = 0 
    
    i = 0 
    for x in sentences:
        #print '\t...finding centrality for sentence #{0}...'.format(i)
        c = 0
        setY = []
        setY.extend(sentences) 
        setY.remove(x) 
        for y in setY:
            c += tf_idf_cosine(x, y, tf, idf)
        
        c = (1/K) * c 
        centralities[x] = c 
        if c > bestC:
            bestC = c 
        i += 1
        
    # Sort centralities, highest first 
    orderedS = sorted(centralities, key=centralities.__getitem__, reverse=True) 
    
    # Return a list of the top sentences 
    # EDIT: Reducing to top sentence, as sentence boundaries are such that a sentence might already be one or two sentences
    return [orderedS[0]], bestC  
    
def tf_idf_cosine(x, y, tf, idf):
    """ Given two sentences x and y, finds tf_idf_cosine(x,y)
    
        Using a model over a document (the set of sentences), and a model over the collection of documents including that document, finds the tf_idf_cosine using the values in those models.
        
        The term frequency (tf) of each term of a sentence is the count it appears in the document, or the number of bigrams including the term in the document model. (given)
        
        The inverse document frequency is the count of the term in the collection model.
        
        Note this then bias the tf_idf_cosine towards greater unique bigrams, and bias against unigram repetition; although it also does not punish terms with unigram repetition as heavily unless it also has a great deal of bigrams.
        
        Refer to p771, eq 23.12 of J&M 
    
    """
    
    # Convert sentences to list of terms
    x = x.split()
    y = y.split() 
    
    # Find each value of tf_idf_cosine equation
    
    SUM_X = 1 
    for term in x:
        tfX = getFreq(tf, term)
        idfX = getFreq(idf, term)
        SUM_X += math.pow(tfX * idfX, 2)
        
    SUM_Y = 1 
    for term in y:
        tfY = getFreq(tf, term)
        idfY = getFreq(idf, term)
        SUM_Y += math.pow(tfY * idfY, 2)
        
    words = []
    words.extend(x) 
    words.extend(y)
    SUM_W = 0 
    for w in words:
        idf_W = 0
        tf_WX = 0 
        tf_WY = 0 
        idf_W = getFreq(idf, w)
        wf = getFreq(tf, w)
        if w in x:
            tf_WX = wf
        if w in y: 
            tf_WY = wf 
            
        SUM_W += tf_WX * tf_WY * idf_W * idf_W 
        
    cosine = SUM_W / (math.sqrt(SUM_X) * math.sqrt(SUM_Y)) 
    
    return cosine 
            
    
def getFreq(freqlist, term):
    if term in freqlist:
        return freqlist[term] 
    else:
        return 0 
    

def checkPath(path):
    if not os.path.exists(path):
        print '\nPath {0} does not exist'.format(path)
        return False
    return True

def printHelp():
    print 'Usage: \npython extract.py -i <input> -o <output>'
    print 'Given ranked results, creates summary from best result'
    print 'Options:'
    print '\t-i <input>\t--input="<input>"\tGive rank result file as input'
    print '\t-o <output>\t--output="<output>"\tName of generated summary file'
    print '\n'

def readResults(fileName):
    lineNum = 1
    lastline = ""
    resultlist = []
    NR = 0 
    ND = 0 
    try:
        file = open(fileName)
        
        queryterms = file.readline().rstrip().split(':')[-1].strip()  # get query terms
        collection = file.readline().rstrip().split(':')
        baseP = float(collection[1].strip())                     # get collection base prob 
        colFile = collection[3].strip()                          # get collection model
        
        recall_numbers = file.readline().rstrip().split(':')
        NR = int(recall_numbers[1].strip())
        ND = int(recall_numbers[3].strip())
        
        skip = file.readline()                                          # skip column headers
        
        # Get each result 
        for line in file:
            if line.strip() == "":
                continue
            lastline = line 
            result = Results()
            result.query = queryterms 
            result.baseP = baseP 
            result.colFile = colFile 
            topResult = line.rstrip().split('|')
            #print 'topResult: ', topResult
            result.rank = int(topResult[0].strip())         # get rank
            #print 'rank: ', result.rank
            result.p = float(topResult[1].strip())          # get result query prob
            #print 'p: ', result.p 
            result.pDiff = result.p - result.baseP 
            #print 'pDiff: ', result.pDiff
            result.originFile = topResult[3].strip()       # get origin document        
            #print 'originFile: ', result.originFile 
            result.modelFile = topResult[2].strip()        # get model file
            #print 'modelFile: ', result.modelFile
            resultlist.append(result)
            #print 'appending'
            
            lineNum += 1
        
        
    except:
        msg = "ERROR reading file: {0} on line {1} of string: {2}".format(fileName, lineNum, lastline)
        
        print msg 
        logging.error(msg)
        
            
    else:
        file.close()
        return resultlist, NR, ND 
        
    return resultlist, NR, ND 

  
def readDoc(filename, result):
    lineNum = 0 
    
    print 'Reading document: {0}'.format(filename)
    
    try:
        file = open(filename) 
         
        # Get the metadata 
        result.link = file.readline().rstrip().lower() 
        result.date = file.readline().rstrip().lower() 
        result.title = file.readline().rstrip().lower() 
         
        # Get sentences 
        for line in file:
            result.sentences.append(line)
            lineNum += 1
        
         
    except:
        print "ERROR reading file: {0} at line number {1}".format(filename, lineNum)
        raise 
    else:
        file.close()

def printRecall(list, NR, ND):
    recall = 0 
    N = len(list)
    for r in list:
        if r.p > r.baseP:
            recall += 1 
            
    print 'Relevant docs total: ', NR
    print 'Total docs: ', ND 
    print 'Recall: ', recall / NR      
    print 'Precision: ', recall / ND    
    print 'In top {1} results, {0} results of {1} relevant, that is PR > BASEPR'.format(recall, N)
    
def printMetrics(list):
    pdiff = list[0].p - list[1].p
    cdiff = list[0].summaryCentrality - list[1].summaryCentrality
    print 'Comparing top two results, PR difference = ', pdiff 
    print 'Comparing centralities, Centrality diffrence = ', cdiff
        
def printSummary(result):
    print '\n\nRank {0} result'.format(result.rank)
    print '-----------'
    print 'Link: ', result.model.link.strip() 
    print 'Title: ', result.model.title.strip() 
    print 'Date: ', result.model.date.strip()
    print 'Summary Centrality: ', result.summaryCentrality 
    print 'Summary: '
    for s in result.summary:
        print s.strip()

def getTopResult(resultFile, summaryFile):
    # Get results
    resultlist, NR, ND = readResults(resultFile)
    
    print 'For query: ', resultlist[0].query
    
    
    # Let us compare the top two results 
    #print resultlist
    top2 = [resultlist[0], resultlist[1]]
    
    # Get document sentences
    for result in top2:
        readDoc(result.originFile, result)
        
        # Get top document model and collective model 
        result.model = rank.readModel(result.modelFile)
        result.colModel = rank.readModel(result.colFile)
        
        # Perform summarization over origin document 
        result.summary, result.summaryCentrality = summarize(result.sentences, result.model, result.colModel)
    
    printRecall(resultlist, NR, ND)
    printMetrics(top2)
    printSummary(resultlist[0])
    printSummary(resultlist[1])
        
def main(argv):
    resultFile = ""              
    summaryFile = ""             
    
    try:
        opts, args = getopt.getopt(argv, "hi:o:",["input=", "output="])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printHelp()
            sys.exit(1)
        elif opt in ('-i', '--input'):
            resultFile = arg 
        elif opt in ('-o', '--output'):
            summaryFile = arg 
            
    if not checkPath(resultFile):
        sys.exit()
    
    getTopResult(resultFile, summaryFile)
   
  
if __name__ == "__main__":
    main(sys.argv[1:])
