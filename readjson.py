import json
import sys
import getopt
import os
import codecs
import nltk

def read(fileName):
    try:
        file = codecs.open(fileName, encoding='utf-8')
        data = json.load(file)
        file.close()
        return data
    except:
        print "ERROR reading {0}".format(fileName)
        raise

def writeDoc(item, fileName):
    try:
        print "Writing doc {0}...".format(fileName)
        file = open(fileName, "w")
        
        link = item['link']
        
        date = item['date']
        if len(date) > 0:
            date = date[0]
        else:
            date="NULL"
        
        title = item['title']
        if len(title) > 0:
            title = title[0]
        else:
            title = "NULL"
        
        body = item['body']
        sentences = []
        if len(body) > 0:
            sentences = cleanBody(body)
        else:
            sentences.append("NULL")
        
        # Make sure to encode unicode characters (converts tokens \uXXXX to right character)
        file.write("{0}\n".format(link.encode('utf-8')))
        file.write("{0}\n".format(date.encode('utf-8')))
        file.write("{0}\n".format(title.encode('utf-8')))
        
        for s in sentences:
            file.write("{0}\n".format(s.encode('utf-8')))
        
        file.close()
    except:
        print "ERROR writing {0}".format(fileName)
        raise
        
def cleanBody(body):
    """
    Clean any other markup, join paragraphs, and separate by sentence
    """
    text = u""
    for p in body:
        text = text + p
    
    # Fetch a tokenizer for sentence segmentation
    sent_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    sentences = sent_tokenizer.tokenize(text)
    
    return sentences
        
        
def printItem(item):
    print "Link: ", item['link']
    print "Date: ", item['date']
    print "Title: ", item['title'] 
    print "First paragraph: \n", item['body'][0]
    print "Second paragraph: \n", item['body'][1]

def printHelp():
    print "\nUsage: python readjson.py -i <inputJsonFile> -o <outputFilePrefix>"
    print "\t-i <inputJsonFile>\t\t*.json file of items to read in"
    print '\talso can do --input="<inputJsonFile>"\n'
    print "\t-o <outputFilePrefix>\t\tFor each item i, file <outputFilePrefix>_[i].txt will contain raw text with one sentence per line"
    print '\talso can do --output="<outputFilePrefix>"\n'
    print "\n"
    
def main(argv):
    outputPath = ""
    jsonFileName = ""

    try:
        opts, args = getopt.getopt(argv, "hi:o:",["input=,output="])
    except getopt.GetoptError:
        printHelp()
        sys.exit(2)
    for opt, arg in opts:  
        if opt=="-h":
            printHelp()
            sys.exit(1)
        elif opt in ("-i", "--input"):
            jsonFileName = arg
        elif opt in ("-o", "--output"):
            outputPath = arg
            
    if not os.path.exists(jsonFileName):
        print '\nPath {0} does not exist'.format(jsonFileName)
        sys.exit()
    
    # Get all data
    data = read(jsonFileName)
    
    # Write each item to a separate doc
    for i in range(len(data)):
        output = outputPath + '_' + repr(i) + '.txt'
        writeDoc(data[i], output)
        
    print "DONE writing docs"
    
  
if __name__ == "__main__":
    main(sys.argv[1:])
