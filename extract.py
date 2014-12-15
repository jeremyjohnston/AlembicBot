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
    for s in sentences:
        centralities[s] = 0 
    
    i = 0 
    for x in sentences:
        print '\t...finding centrality for sentence #{0}...'.format(i)
        c = 0
        setY = []
        setY.extend(sentences) 
        setY.remove(x) 
        for y in setY:
            c += tf_idf_cosine(x, y, tf, idf)
        
        c = (1/K) * c 
        centralities[x] = c 
        i += 1
        
    # Sort centralities, highest first 
    orderedS = sorted(centralities, key=centralities.__getitem__, reverse=True) 
    
    # Return a list of the top sentences 
    # EDIT: Reducing to top sentence, as sentence boundaries are such that a sentence might already be one or two sentences
    return [orderedS[0]] 
    
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
    result = Results()
    try:
        file = open(fileName)
        
        result.query = file.readline().rstrip().split(':')[-1].strip()  # get query terms
        collection = file.readline().rstrip().split(':')
        result.baseP = float(collection[1].strip())                     # get collection base prob 
        result.colFile = collection[3].strip()                          # get collection model
        skip = file.readline()                                          # skip column headers
        topResult = file.readline().rstrip().split('|')                  
        result.p = float(topResult[1].strip())                          # get result query prob
        result.pDiff = result.p - result.pDiff                           
        result.originFile = topResult[-1].strip()                       # get origin document        
        result.modelFile = topResult[-2].strip()                        # get model file
        
        
    except:
        msg = "ERROR reading file: {0}".format(fileName)
        print msg 
        logging.error(msg)
        
            
    else:
        file.close()
        return result

  
def readDoc(filename, result):
    lineNum = 0 
    
    print 'Reading document: {0}'.format(filename)
    
    try:
        file = open(filename) 
         
        # Get the metadata 
        result.link = file.readline().rstrip().lower() 
        result.date = file.readline().rstrip().lower() 
        result.title = file.readline().rstrip().lower() 
         
        # Process each sentence for unigram and bigram features
        for line in file:
            result.sentences.append(line)
            lineNum += 1
        
         
    except:
        print "ERROR reading file: {0} at line number {1}".format(filename, lineNum)
        raise 
    else:
        file.close()

def printSummary(result):
    print 'Top result'
    print '-----------'
    print 'Link: ', result.model.link.strip() 
    print 'Title: ', result.model.title.strip() 
    print 'Date: ', result.model.date.strip()
    print 'Summary: '
    for s in result.summary:
        print s.strip()
        
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
    
    printSummary(result)
   
    
    # Evaluate summarization
    
    
    
if __name__ == "__main__":
    main(sys.argv[1:])
