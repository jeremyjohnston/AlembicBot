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
        self.link 
        self.date 
        self.title
        

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
    
    # First fetch idf of each term in colModel, the count of the term
    idf = {} 
    for unigram in colModel.unigrams:
        idf[unigram.word] = unigram.count
        
    # Fetch term frequencies; the number of bigrams here 
    tf = {} 
    for unigram in model.unigrams: 
        tf[unigram.word] = len(unigram.bigrams) 
        
    K = len(sentences) 
    
    # Find centrality values 
    centralities = {}
    for s in sentences:
        centralities[s] = 0 
        
    for x in sentences:
        c = 0
        setY.extend(sentences) 
        setY.remove(x) 
        for y in setY:
            c += tf_idf_cosine(x, y, tf, idf)
        
        c = (1/K) * c 
        centralities[x] = c 
        
    # Sort centralities, highest first 
    
    
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
    
    SUM_X = 0 
    for term in x:
        tfX = getFreq(tf, term)
        idfX = getFreq(idf, term)
        SUM_X += math.pow(tfX * idfX, 2)
        
    SUM_Y = 0 
    for term in y:
        tfY = getFreq(tf, term)
        idfY = getFreq(idf, term)
        SUM_Y += math.pow(tfY * idfY, 2)
        
    
    words = x.extend(y)
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
    else
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
    result = Results()
    try:
        file = open(fileName)
        
        result.query = file.readline().rstrip().split(':')[-1]        # get query terms
        collection = file.readline().rstrip().split(':')
        result.baseP = float(collection[1])                           # get collection base prob 
        result.colFile = collection[3]                                # get collection model
        skip = file.readline()                                        # skip column headers
        topResult = file.readline().rstrip().split('|')
        result.p = float(topResult[1])                                # get result query prob
        result.pDiff = result.p - result.pDiff
        result.originFile = topResult[-1]                             # get origin document
        result.modelFile = topResult[-2]                              # get model file
        
        
    except:
        msg = "ERROR reading file: {0}".format(fileName)
        print msg 
        logging.error(msg)
        
            
    else:
        file.close()
        return result

  
def readDoc(filename, result):
    try:
        file = open(filename)
        lineNum = 0 
         
        # Get the metadata 
        result.link = file.readline().rstrip().lower() 
        result.date = file.readline().rstrip().lower() 
        result.title = file.readline().rstrip().lower() 
         
        # Process each sentence for unigram and bigram features
        for line in file:
            result.sentences.extend(line)
            lineNum += 1
        
         
    except:
        print "ERROR reading file: {0} at line number {1}".format(filename, lineNum)
        raise 
    else:
        file.close()
        
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
    
    # Get results
    result = readResults(resultFile)
    
    # Get top document sentences
    readDoc(result.originFile, result)
    
    # Get top document model and collective model 
    result.model = rank.readModel(result.modelFile)
    result.colModel = rank.readModel(result.colFile)
    
    # Perform summarization over origin document 
    result.summary = summarize(result.sentences, result.model, result.colModel)
    
    # Evaluate summarization
    
    
    
if __name__ == "__main__":
    main(sys.argv[1:])
