#!/usr/bin/python2.7
# Jeremy Johnston

"""
Tests and evaluates a model file on classifying a set of files.

Given a Naive Bayes model file, and a list of positive and negative files,
performs 10-fold cross validation.

"""

from __future__ import division 
import sys
import getopt
import os
import math
from collections import deque
import time
import logging
from genModel import Unigram, Bigram, FeatureSet


logging.basicConfig(filename="rank.log", level=logging.DEBUG)

def readDirectory(dir):
    names = []
    models = []
    try:
        names = os.listdir(dir)
        names.sort()
        for name in names:
            file = os.path.join(dir, name)
            models.append(readModel(file))
    except:
        print "ERROR reading directory at path {0}".format(dir)
        raise
    finally:
        return models

def readModel(fileName):
    posSet = FeatureSet(polarity=1)
    negSet = FeatureSet(polarity=0)
    lineNum = 1
    mode = 0
    
    try:
        file = open(fileName)
        
        for line in file:
            line.rstrip()
            if line == "positive probabilities:\n":
                mode = 1
            elif line == "negative probabilities:\n":
                mode = 2
            else:         
                # Add probabilities to posSet
                if mode is 1:
                   
                    tokens = line.split()
                    
                    # Format: probability word count
                    if len(tokens) == 3:  
                        prob = float(tokens[0])
                        word = tokens[1]
                        count = int(tokens[2])
                        posSet.words[word] = Unigram(word=word, count=count, probability=prob)
                    # Format: probability word1 word2 count
                    else:
                        prob = float(tokens[0])
                        word1 = tokens[1]
                        word2 = tokens[2]
                        count = int(tokens[3])
                        posSet.words[word1].bigrams[word2] = Bigram(probability=prob, word1=word1, word2=word2, count=count)
                        
                
                # Add probabilities to negSet
                elif mode is 2:
                    
                    tokens = line.split()
                    
                    # Format: probability word count
                    if len(tokens) == 3:  
                        prob = float(tokens[0])
                        word = tokens[1]
                        count = int(tokens[2])
                        negSet.words[word] = Unigram(word=word, count=count, probability=prob)
                    # Format: probability word1 word2 count
                    else:
                        prob = float(tokens[0])
                        word1 = tokens[1]
                        word2 = tokens[2]
                        count = int(tokens[3])
                        negSet.words[word1].bigrams[word2] = Bigram(probability=prob, word1=word1, word2=word2, count=count)
                    
            lineNum += 1
                
    except:
        print "ERROR: Problem reading file {0} on line {1}".format(fileName, lineNum)
        raise
    else:
        file.close()
        return posSet, negSet

def processUnigram(word, vector):
    unigram, exists = vector.getUnigram(word)
    if not exists:
        vector.addUnigram(word)        
        
def processFeature(prevWord, word, vector):
    # If n-grams exist in vector, skip as we only care about presence of feature in file, not duplicates 
    
    unigram, exists = vector.getUnigram(prevWord)
    if not exists:
        vector.addUnigram(prevWord)
        
    bigram, exists = vector.getBigram(prevWord, word)
    if not exists:
        vector.addBigram(prevWord, word)        
        
# TODO - rewrite for testing
def evaluateTestFile(filename, posModel, negModel):
    guess = 0 
    
    try:
        file = open(filename)
        lineNum = 0 
        
        # Feature set just for this file; polarity of vector doesn't matter, as we'll evaluate it against both
        vector = FeatureSet(0)
        
        # Process each sentence for unigram and bigram features
        for line in file:
            line.rstrip()
            tokens = line.split()
            
            vector.numTokens += len(tokens)
            
            # Handle special case of 1 token
            if len(tokens) == 1 :
                processUnigram(tokens[0], vector)
            # Handle normal line of at least two tokens (for zero tokens we do nothing)        
            elif len(tokens) >= 2 :
                q = deque(tokens)
                
                
                
                prevWord = q.popleft()
                word = q.popleft() 
                
                processFeature(prevWord, word, vector) 
                
                prevWord = word 
                
                for t in q:
                    word = t 
                    
                    processFeature(prevWord, word, vector)
                    
                    prevWord = word 
                
            lineNum += 1
        
        # Compare vectors naive bayes value of each model, and make a guess 
        class0 = negModel.naiveBayes(vector)
        class1 = posModel.naiveBayes(vector) 
        
        if class0 > class1:
            guess = 0 
        else:
            guess = 1
            
         
    except:
        print "ERROR reading file: {0} at line number {1}".format(filename, lineNum)
        raise 
    else:
        file.close()
        return guess 

def review_with_10fold_validation(polarity, directory, posModels, negModels):        
    names = []
    parts = [[0]] * 10
    accuracies = [0] * 10  
    
    try:
        names = os.listdir(directory)
        names.sort()   
        
        logging.debug("Sorted file names of directory {0} are: {1}".format(directory, names))
        
        size = len(names)
        subsetSize = math.floor(size / 10)
        
        for i in range(10):
            start = int(subsetSize * i) 
            end = int(subsetSize * (i+1)) 
            parts[i] = names[start:end]
            
            # Test part[i] against models[i], which are trained over all parts not part i 
            accuracies[i] = reviewFiles(polarity, directory, parts[i], posModels[i], negModels[i])
        
            
    except:
        print 'Problem reviewing directory {0}'.format(directory)
        raise
        
    else:
        # Later we average the positive accuracies against the negative accuracies to get our 10 accuracies
        return accuracies 

    
def reviewFiles(polarity, directory, filenames, posModel, negModel):
    correct = 0 
    
    try:
       
        logging.debug("Reviewing all files in directory: {0}, file names are: {1}".format(directory, filenames))
        
        for name in filenames:
            fullPath = os.path.join(directory, name)
            guess = evaluateTestFile(fullPath, posModel, negModel)
            if guess == polarity:
                correct += 1 
        
    except:
        print "ERROR: Problem reading files in directory at path {0}".format(directory)
        raise   
    else:
        acc = correct / len(filenames)
        return acc 

def sortDirectory(directory):
    names = []
    try:
        names = os.listdir(directory)
        names.sort()
        #TODO: Turn into cross-validation subset
        
    except:
        print 'Error reading and sorting directory: {0}'.format(directory)
        raise
    else:
        return names

def printHelp():
    print 'Usage: \npython rank.py -d <dir> -c <col> -q <query> -o <outputFileName>'
    print 'Program will rank documents based on given query, where rank #1 is best document.'
    print 'Options:'
    print '\t-d <dir>\t--dir="<dir>"\Give directory of individual model files to read'
    print '\t-c <col>\t--col="<col>"\Give model file over a collection to read'
    print '\t-o <outputFileName>\t--output="<outputFileName>"\tFile to write rank results in'
    print '\t-q <query>\t--query="<query>"\tWhite space separated query terms'

def checkPath(path):
    if not os.path.exists(path):
        print '\nPath {0} does not exist'.format(path)
        return False
    return True
        
def main(argv):
    dir = ""                # Directory of individual models 
    col = ""                # Path to model over collection 
    outputFileName = ""     # Where to write report of ranks 
    query = ""              # Query text
    
    try:
        opts, args = getopt.getopt(argv, "hd:c:q:o:",["dir=", "col=", "query=", "output="])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printHelp()
            sys.exit(1)
        elif opt in ('-d', '--dir'):
            dir = arg 
        elif opt in ('-c', '--col'):
            col = arg 
        elif opt in ('-o', '--output'):
            outputFileName = arg
        elif opt in ('-q', '--query'):
            query = arg
            
    if not checkPath(dir) or not checkPath(col):
        sys.exit()
     
    start = time.clock()
    
    terms = query.split()
    if len(terms) < 1:
        print "Please give query terms, space delimited"
        print "exiting..."
        sys.exit()
    
    # Read model files
    models = readDirectory(dir)
    colModel = readModel(col)
    
    # Rank using mixture model equation. We need to find best lambda using a dev set of data.
    # Rank will return a list of the top N models.
    results = rank(terms, models, colModel)
    
    # Write out the top N model data 
    writeReport(results)
    
    end = time.clock() - start
    print 'Time of execution: {0} seconds'.format(end)
    print 'DONE\n\n'

if __name__ == "__main__":
    main(sys.argv[1:])