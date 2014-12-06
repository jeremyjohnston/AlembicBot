import json
import sys
import getopt
import os


def read(fileName):
    file = open(fileName)
    data = json.load(file)
    
    return data

def printItem(item):
    print "Link: ", item['link']
    print "Date: ", item['date']
    print "Title: ", item['title'] 
    print "First paragraph: \n", item['body'][0]
    print "Second paragraph: \n", item['body'][1]
    
def main(argv):
    jsonFileName = ""

    try:
        opts, args = getopt.getopt(argv, "f:",["file="])
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in opts:  
        if opt in ("-f", "--file"):
            jsonFileName = arg
            
    if not os.path.exists(jsonFileName):
        print '\nPath {0} does not exist'.format(jsonFileName)
        sys.exit()
        
    data = read(jsonFileName)
    
    print "Items: ", len(data)
    print "First item\n---\n "
    printItem(data[0])
    
  
if __name__ == "__main__":
    main(sys.argv[1:])
