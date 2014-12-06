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
        date = item['date'][0]
        title = item['title'][0]
        
        body = item['body']
        sentences = cleanBody(body)
        
        file.write("{0}\n".format(link))
        file.write("{0}\n".format(date))
        file.write("{0}\n".format(title))
        
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
    
def main(argv):
    jsonFileName = ""
    outputFileName = ""

    try:
        opts, args = getopt.getopt(argv, "i:o:",["input=,output="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:  
        if opt in ("-i", "--input"):
            jsonFileName = arg
        elif opt in ("-o", "--output"):
            outputFileName = arg
            
    if not os.path.exists(jsonFileName):
        print '\nPath {0} does not exist'.format(jsonFileName)
        sys.exit()
        
    data = read(jsonFileName)
    
    print "Items: ", len(data)
    print "First item\n---\n "
    printItem(data[0]) 
    
    writeDoc(data[0], outputFileName)
    print "DONE writing docs"
    
  
if __name__ == "__main__":
    main(sys.argv[1:])
