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
        
def main(argv):
    posDir = ""   
    negDir = ""      
    modelFile = ""
    
    try:
        opts, args = getopt.getopt(argv, "hp:n:m:",["posDir=", "negDir=", "model="])
    except getopt.GetoptError:
        print 'Usage: \npython testNB.py -p <posDir> -n <negDir> -m <modelFilePrefix>'
        print 'or'
        print 'python testNB.py --posDir="<posDir>" --negDir="<negDir>" --model="<modelFilePrefix>"'
        print '\n<posDir> is directory of positive files, \n<negDir> directory of negative files, and \n<modelFile> the prefix of the 10 model files to use for testing.\nModel files are expected of form <prefix>_[0-9].nb to be used for 10 fold validation'
        print '\nNote that directory reading is not recursive.'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'Usage: \npython testNB.py -p <posDir> -n <negDir> -m <modelFilePrefix>'
            print 'or'
            print 'python testNB.py --posDir="<posDir>" --negDir="<negDir>" --model="<modelFilePrefix>"'
            print '\n<posDir> is directory of positive files, \n<negDir> directory of negative files, and \n<modelFile> the prefix of the 10 model files to use for testing.\nModel files are expected of form <prefix>_[0-9].nb to be used for 10 fold validation'
            print '\nNote that directory reading is not recursive.'
            sys.exit(1)
        elif opt in ('-p', '--posDir'):
            posDir = arg 
        elif opt in ('-n', '--negDir'):
            negDir = arg 
        elif opt in ('-m', '--model'):
            modelFile = arg
            
    if not os.path.exists(posDir):
        print '\nPath {0} does not exist'.format(posDir)
        sys.exit()
    
    if not os.path.exists(negDir):
        print '\nPath {0} does not exist'.format(negDir)
        sys.exit()
    
    modelFiles = [""] * 10 
    for i in range(10):
        modelFiles[i] = modelFile + '_' + repr(i) + '.nb' 
        
        if not os.path.exists(modelFiles[i]):
            print '\nPath {0} does not exist'.format(modelFiles[i])
            sys.exit() 
    
    start = time.clock()
        
    # Read model files
    posModels = [0] * 10 
    negModels = [0] * 10 
    
    for i in range(10):
        print 'Reading model file {0}...'.format(modelFiles[i])
        posModels[i], negModels[i] = readModel(modelFiles[i])
    
    posacc = [0] * 10 
    negacc = [0] * 10 
    acc = [0] * 10 
    
    posacc = review_with_10fold_validation(1, posDir, posModels, negModels)
    negacc = review_with_10fold_validation(0, negDir, posModels, negModels) 
    overallAccuracy = 0 
    for i in range(10):
        acc[i] = (posacc[i] + negacc[i]) / 2
        overallAccuracy += acc[i]
    
    overallAccuracy = overallAccuracy / 10 
    
    
    
    # Sort files into subset for training
    # posFiles = sortDirectory(posDir)
    # negFiles = sortDirectory(negDir)
    
    # # Read and evaluate each positive and negative document with Naive Bayes
    # print 'Testing over directory {0}...'.format(posDir)
    # acc1 = reviewFiles(1, posDir, posFiles, posModel, negModel)
    
    # print 'Testing over directory {0}...'.format(negDir)
    # acc2 = reviewFiles(0, negDir, negFiles, posModel, negModel)
    
    # # Report average accuracy of model file over documents
    # avg = (acc1 + acc2) / 2
    
    end = time.clock() - start
    print 'Time of execution: {0} seconds'.format(end)
    #print 'Accuracy over negative and positive documents: {0} , found in {1} seconds'.format(avg, end)
    print 'Accuracies: {0}'.format(acc) 
    print 'Average accuracy: {0}'.format(overallAccuracy)    

if __name__ == "__main__":
    main(sys.argv[1:])