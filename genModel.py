#!/usr/bin/python2.7
# Jeremy Johnston

""" Generates a language model file from given data.

"""

from __future__ import division
import sys
import getopt
import os
import math
from collections import deque
import time
import logging

logging.basicConfig(filename="genModel.log", level=logging.DEBUG)

class FeatureSet():
    def __init__(self, polarity):
        self.words = {} # dictionary of (word, unigram) pairs, and our feature set
        self.numTokens = 0 
        self.polarity = polarity
    
    def getUnigram(self, word1):
        unigram = Unigram("NULL_DNE", 0, 0)
        boolFound = False 
        
        if word1 in self.words:
            unigram = self.words[word1] 
            boolFound = True 
            
        return unigram, boolFound
    
    def getBigram(self, word1, word2):
        """ Return a pair (bigram, boolFound)
        """
    
        bigram = Bigram("NULL_DNE", "NULL_DNE", 0, 0)
        boolFound = False 
        
        if word1 in self.words:
            if word2 in self.words[word1].bigrams:
                bigram = self.words[word1].bigrams[word2]
                boolFound = True 
                
        return bigram, boolFound

    def addUnigram(self, word):
        boolExists = False
        
        if word in self.words:
            self.words[word].count += 1 
            boolExists = True
        else:
            self.words[word] = Unigram(word, count=1, probability=0)
        
        return boolExists
        
    def addBigram(self, word1, word2):
        boolExists = False
        
        if word1 in self.words:
            
            # Commented out - don't count more than once per document, so addUnigram should have already counted.
            #self.words[word1].count += 1
            
            if word2 in self.words[word1].bigrams:
                self.words[word1].bigrams[word2].count += 1 
                boolExists = True
            else:
                self.words[word1].bigrams[word2] = Bigram(word1, word2, count=1, probability=0)
                
        else:
            self.words[word] = Unigram(word, count=1, probability=0)
            self.words[word1].bigrams[word2] = Bigram(word1, word2, count=1, probability=0)
            
        return boolExists
     
    def updateUnigrams(self, unigram):
        # Tally counts to model
        if self.addUnigram(unigram.word):
            # Compensate for one count of addUngiram
            self.words[unigram.word].count += unigram.count - 1  
    
    def updateBigrams(self, bigram):
       # Tally counts to model
        if self.addBigram(bigram.word1, bigram.word2):
            # Compensate for one count of addBigram
            self.words[bigram.word1].bigrams[bigram.word2].count += bigram.count - 1
     
    def update(self, vector):
    
        self.numTokens += vector.numTokens
    
        for unigram in vector.words.itervalues():
            self.updateUnigrams(unigram)
            for bigram in unigram.bigrams.itervalues():
                self.updateBigrams(bigram)
            
    def calculateProbabilities(self):
        ''' Finds Log MLE Probability of each feature.
        
            Probability of feature_i in class_j is: 
                P(feature_i | class_j) = (count(feature_i, class_j) / total_count(f)
            using a bag-of-words model where if a word occurs in a document at least once, we increment the count of that word (feature) once, ignoring duplicates.
            
            Note then the probabilities are then not normalized, but as we only care about their maximum in testing, this is ok.
            
            Our features are Unigrams and Bigrams.
        '''
        
        # We'll use add-k smoothing, k <= 1
        k = 1               # smoothing constant
        V = len(self.words) # vocab size
        for unigram in self.words.itervalues():
            unigram.probability =  (unigram.count + k) / (self.numTokens + V)
            #unigram.probability =  (unigram.count) / (self.numTokens)
            unigram.probability = math.log(unigram.probability, 2)
        
            # TODO DEBUG did add one to denominator as well, unsure if necessary
            for bigram in unigram.bigrams.itervalues():
                bigram.probability = (bigram.count + k) / (unigram.count + V) 
                #bigram.probability = (bigram.count) / (unigram.count) 
                bigram.probability = math.log(bigram.probability, 2)
                
    def naiveBayes(self, vector):
        """ Perform Naive Bayes evaluation over the given vector
        
            The typical equation is:
                class_nb = argmax(c) P(c) * PRODUCT_all_i[ P(xi | c) ]
                
            However here we return the value for the class of this model, polarity,
            and use log probabilities. Also, assuming binary classes 0 and 1, we can drop
            the requirement to use P(c). So then we return:
                SUM_all_i[ log P(xi | c) ]
                
            and let caller compare two naiveBayes result to determine argmax.
                
        """
        
        # Find product of all Unigram and Bigram probabilities, which are already converted to log probabilities
        value = 0 
        for word1 in vector.words.iterkeys():
            unigram, unigramExists = self.getUnigram(word1)
            if unigramExists:
                value += self.words[word1].probability
            else:
                # Use add one smoothing for unseen events, P(unseen) = 1 / (numSeenInstances + sizeVocab)  
                value += math.log(1 / (self.numTokens + len(self.words)), 2)
            for word2 in vector.words[word1].bigrams.iterkeys():
                bigram, bigramExists = self.getBigram(word1, word2) 
                if bigramExists:
                    value += self.words[word1].bigrams[word2].probability
                else:
                    # Use add one smoothing for unseen events, P(unseen) = 1 / (numSeenInstances + sizeVocab)
                    count = 0 
                    if word1 in self.words:
                        count = self.words[word1].count 
                    else:
                        count = 1 
                    value += math.log(1 / (count + len(self.words)), 2)
                    
        return value
            
    
class Unigram():
    def __init__(self, word, count, probability):
        self.word = word 
        self.count = count 
        self.probability = probability
        
        # Let a unigram word keep track of it's bigrams
        self.bigrams = {} # Pairs (Word2, Bigram) for this unigram Word1
        
class Bigram():
    def __init__(self, word1, word2, count, probability):
        self.word1 = word1      # Word W_i
        self.word2 = word2      # Word W_i+1
        self.count = count 
        self.probability = probability

###################################################################################################
###################################################################################################

def processUnigram(word, vector):
    """ Adds feature to vector or increases its count in vector
    """

    unigram, exists = vector.getUnigram(word)
    vector.addUnigram(word)
    
def processFeature(prevWord, word, vector):
    """ Adds feature to vector or increases its count in vector
    """
    
    # We add feature whether it exists or not
    unigram, exists = vector.getUnigram(prevWord)
    if not exists:
        vector.addUnigram(prevWord)
  
        
    bigram, exists = vector.getBigram(prevWord, word)
    if not exists:
        vector.addBigram(prevWord, word)
   
        
    
    
def readFile(filename, model):
    try:
        file = open(filename)
        lineNum = 0 
        
        # Feature set just for this file
        vector = FeatureSet(model.polarity)
        
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
        
        # Tally each feature in vector and add to model
        model.update(vector)
         
    except:
        print "ERROR reading file: {0} at line number {1}".format(filename, lineNum)
        raise 
    else:
        file.close()

def read_with_10fold_validation(directory, models):
    names = []
    parts = [[]] * 10
    subsets = [[]] * 10
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
            
        for i in range(10):
            subsets[i] = [n for n in names if n not in parts[i] ]
            readReviewDirectory(directory, subsets[i], models[i])
        
        
        
    except:
        print "ERROR: Problem reading directory at path {0}".format(directory)
        raise 
        
def readReviewDirectory(directory, fileNames, model):
 
    try:       
        for name in fileNames:
            fullPath = os.path.join(directory, name)
            readFile(fullPath, model)
        
    except:
        print "ERROR: Problem reading directory at path {0}".format(directory)
        raise 

def writeModelFile(modelFile, model):
    try:
        file = open(modelFile, 'w')
        
        # Write probabilities
        
        for unigram in model.words.itervalues():
            # Write the unigram probability 
            file.write('{0} {1} {2}\n'.format(unigram.probability, unigram.word, unigram.count))
            
            # Then the bigrams for that word
            for bigram in unigram.bigrams.itervalues():
                file.write('{0} {1} {2} {3}\n'.format(bigram.probability, bigram.word1, bigram.word2, bigram.count))
        
        
                
    except:
        print 'ERROR writing model file {0}'.format(modelFile)
        raise
    else:
        file.close()

def modeEach(dir, modelFilePrefix):
    print "\nStarting modeEach, generate model for each doc in ", dir
    # Get doc names 
    names = []
    try:
        names = os.listdir(dir)
        names.sort()   
        logging.debug("Sorted file names of directory {0} are: {1}".format(dir, names))
    except:
        print "ERROR: Problem reading directory at path {0}".format(dir)
        raise 

    models = [] 
    
    # Read, process, and write each in turn. The upside here is in case of failure, we can resume from the point of failure.
    for i in range(len(names)):
        models.append(FeatureSet(polarity = 1))
        fullPath = os.path.join(dir, names[i])
        # Read each file, counting unigrams and bigrams as we do
        print 'Reading file {0}...'.format(fullPath)
        readFile(fullPath, models[i])
    
        # Find Log MLE probabilities based on counts
        print '\tCalculating log MLE probabilities of unigram and bigram features...'
        models[i].calculateProbabilities()
        
        # Write to model file
        fileName = modelFilePrefix + '_' + repr(i) + '.model'
        print '\tWriting to model file: {0}...'.format(fileName)
        writeModelFile(fileName, models[i])
    
def printHelp():
    print "\nUsage: python genModel.py -d <dir> -m <modelFilePrefix> -a"
    print "Operation: Generate a model for collection of documents in directory <dir> with model file name of <modelFilePrefix>_all.model"
    print 'Options: '
    print '\t-d <dir>\t\tSpecify directory of document collection'
    print '\t--dir="<dir>"\t\tSame as above'
    print '\n'
    print '\t-m <modelFilePrefix>\t\tSpecify name of output model file (in all mode) or prefix of each file (in individual mode)'
    print '\t--model="<modelFilePrefix>"\t\tSame as above. Output files will be of name <modelFilePrefix>.model'
    print '\n'
    print '\t-i\t\tSpecify execution mode "individual". Generates model file for each document in directory <dir>, of names <modelFilePrefix>[0-N].model'
    print '\n'
    print '\t-b\t\tSpecify execution mode "both". Generates model file for each document in directory <dir>, of names <modelFilePrefix>[0-N].model and model over all docs.'
    print '\n'
    print '\t-a\t\tSpecify execution mode "all". Generates model file for whole collection in <dir>, of name <modelFilePrefix>_all.model'
    print '\n\n'
        
def main(argv):
    
    # Whether model is all or each(individual). Mode both is when both are true
    MODE_ALL = False
    MODE_EACH = False
    
    dir = ""                # Directory of documents   
    modelFilePrefix = ""    # Prefix of model files to be written
   
    
    try:
        opts, args = getopt.getopt(argv, "hd:m:iab",["dir=", "model="])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            printHelp()
            sys.exit(1)
        elif opt == '-i':
            MODE_EACH = True
        elif opt == '-a':
            MODE_ALL = True
        elif opt == '-b':
            MODE_ALL = True
            MODE_EACH = True
        elif opt in ('-d', '--dir'):
            dir = arg 
        elif opt in ('-m', '--model'):
            modelFilePrefix = arg 
        
            
    if not os.path.exists(dir):
        print '\nPath {0} does not exist'.format(dir)
        sys.exit()
    
    if not MODE_ALL and not MODE_EACH:
        print '\nERROR: Please give a mode, -i, -a, or -b.'
        printHelp() 
        sys.exit(2)
    
    start = time.clock()
    
    if MODE_EACH:
        logging.info('\nStarting modeEach()...')
        modeEach(dir, modelFilePrefix)
        logging.info('\nFinished modeEach()...')
    
    end = time.clock() - start
    print 'Finished generating model files in time: {0}'.format(end)
    logging.info('\nGeneration done in time {0}\nDONE\n\n'.format(end))
    print '\nDONE\n\n'
    
    
if __name__ == "__main__":
    main(sys.argv[1:])