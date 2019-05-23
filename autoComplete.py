################################################################
# Application Name : autoComplete
# Author : Kartihck S
# Date : 2019-03-16
# OS : Mac, Ubuntu
# Version : 1.0
################################################################
# Importing Required Libraries
import sys
from sklearn.feature_extraction.text import CountVectorizer
import curses
import os
import zerorpc

# Declaring some global variables for later usage
result_list = []
tagKey = ''
flag = False
myLocalString = ''
lengthOfLastWord = 0

# Class which represent TRIE data structure
class Node:
    def __init__(self):
        self.next = {}  #Initialize an empty hash (python dictionary)
        self.word_marker = False

    def add_item(self, string):
        ''' Method to add a string to the Trie data structure'''
        if len(string) == 0:
            self.word_marker = True
            return

        key = string[0] #Extract first character
        string = string[1:] #Create a string by removing first character

        if key in self.next:
            self.next[key].add_item(string)
        else:
            node = Node()
            self.next[key] = node
            node.add_item(string)

    def dfs(self, found=None):
        '''Perform Depth First Search Traversal'''
        if self.next.keys() == []:
            print ("Match DFS Empty :",found)
            return

        if self.word_marker == True:
            #print ("Match DFS :",found)
            result_list.append(found)

        for key in self.next.keys():
            self.next[key].dfs(found + key)

    def search(self, string, found=""):
        '''Perform auto completion search and print the autocomplete results'''
        del result_list[:]
        if len(string) > 0:
            key = string[0]
            string = string[1:]
            if key in self.next:
                found = found + key
                self.next[key].search(string,found)
            else:
                print ("No match")
        else:
            if self.word_marker == True:
                print ("Match Search :",found)

            for key in self.next.keys():
                self.next[key].dfs(found+key)

# Function to parse a file and generate TRIE data structure
def fileparse(filename):
    '''Parse the input dictionary file and build the trie data structure'''
    fd = open(filename)

    root = Node()
    line = fd.readline().strip('\r\n') # Remove newline characters \r\n

    while line !='':
        root.add_item(line)
        line = fd.readline().strip('\r\n')

    return root

# Class which generates bi-grams and helps in predicting next word
class Suggestion:

    def loadaslist(self, filename):
        '''Load contents of file and return it as list'''
        fp = open(filename,'r')
        lines = fp.readlines()
        lines = [line.strip('\r\n').strip() for line in lines]
        lines = [x.lower() for x in lines]
        fp.close()
        return lines

    def initializelist(self):
        '''Initialize various list which hold sections of data'''
        self.players = list(set(self.loadaslist('input/players.txt')))
        self.stadiums = list(set(self.loadaslist('input/stadiums.txt')))
        self.teams = list(set(self.loadaslist('input/teams.txt')))
        self.keywords = list(set(self.loadaslist('input/keywords.txt')))

    def generatematrix(self, filename):
        '''Generate Co-Occurrence Matrix with Bi-Grams'''
        # Read the contents of file which has our corpus
        fp = open(filename,'r')
        lines = fp.readlines()
        lines = [line.strip('\r\n') for line in lines]
        fp.close()

        # Calculate co-occurrence matrix
        count_model = CountVectorizer(ngram_range=(2,2))
        X = count_model.fit_transform(lines)
        Xc = (X.T * X)
        Xc.setdiag(0)
        self.initializelist()
        return Xc, count_model

    def searchList(self, key):
        '''Search for the word typed in text box and return the matching list'''
        for item in key.split(' '):
            if any(item in s for s in self.teams):
                return ('teams',self.teams)
            elif any(item in s for s in self.players):
                return ('players',self.players)
            elif any(item in s for s in self.stadiums):
                return ('stadiums',self.stadiums)
            elif any(item in s for s in self.keywords):
                return ('keywords',self.keywords)

    def getsuggestion(self, Xc, count_model, string):
        '''Predict the next word frmo Co-Occurrence Matrix'''
        # Suggest the words that occurred mostly with the typed word
        del result_list[:]
        global tagKey
        try :
            myColumn = Xc.todense()[count_model.vocabulary_[string]]
        except Exception as e:
            return
        myColumn = myColumn.tolist()[0]
        maxValue = max(myColumn)
        lowerBound = maxValue - 2
        for key, value in count_model.vocabulary_.items():
            if value == myColumn.index(maxValue):
                tagKey, mySuggestionList = self.searchList(key)
                result_list.append([x for x in mySuggestionList])
                maxValue = maxValue - 1
                break

# Class which communicates with Node JS and get events form Client
class Callable(Node, Suggestion, object):

    def __init__(self):
        '''Initialize all trees in out dataset'''
        self.players_tree = fileparse('input/players.txt')
        self.stadiums_tree = fileparse('input/stadiums.txt')
        self.teams_tree = fileparse('input/teams.txt')
        self.keywords_tree = fileparse('input/keywords.txt')
        self.myObj = Suggestion()
        self.Xc, self.count_model = self.myObj.generatematrix('input/sentence.txt')

    def predictnextword(self, word):
        '''Call a tree for spelling assistent / Call redict next word depending on certain conditions'''
        if len(word['word'].split(' ')) == 0:
            return []
        elif len(word['word'].split(' ')) < 3 and len(word['word']) > 0:
            self.keywords_tree.search(word['word'])
            return result_list
        else:
            word_split = word['word'].strip().split(' ')
            word_split = [x.lower() for x in word_split]
            lengthOfWord = len(word_split)
            if len(word_split[(lengthOfWord - 2):]) < 2:
                return []
            else:
                global flag
                global tagKey
                global myLocalString
                global lengthOfLastWord
                if flag == False:
                    generated_word = word_split[lengthOfWord - 2] + ' ' + word_split[lengthOfWord - 1]
                    self.myObj.getsuggestion(self.Xc, self.count_model, generated_word)
                    if len(result_list) != 0:
                        flag = True
                        return result_list[0]
                    else:
                        return []
                else:
                    word_split = word['word'].split(' ')
                    lengthOfWord = len(word_split)
                    if len(myLocalString) == 0:
                        myLocalString = word_split[lengthOfWord - 1]
                    elif len(word['word']) > lengthOfLastWord:
                        myLocalString = myLocalString + word['word'][-1]
                        lengthOfLastWord = len(word['word'])
                    else:
                        myLocalString = myLocalString[:-1]
                        lengthOfLastWord = len(word['word'])

                    if (any(myLocalString.lower() in s for s in self.myObj.players)) and (tagKey == 'players'):
                        self.players_tree.search(myLocalString)

                    elif (any(myLocalString.lower() in s for s in self.myObj.teams)) and (tagKey == 'teams'):
                        self.teams_tree.search(myLocalString)

                    elif (any(myLocalString.lower() in s for s in self.myObj.stadiums)) and (tagKey == 'stadiums'):
                        self.stadiums_tree.search(myLocalString)

                    elif (any(myLocalString.lower() in s for s in self.myObj.keywords)) and (tagKey == 'keywords'):
                        self.keywords_tree.search(myLocalString)

                    if len(result_list) == 0:
                        lengthOfLastWord = 0
                        tagKey = ''
                        myLocalString = ''
                        flag = False

                    return result_list

if __name__ == '__main__':
    players_tree = fileparse('input/players.txt')
    stadiums_tree = fileparse('input/stadiums.txt')
    teams_tree = fileparse('input/teams.txt')
    keywords_tree = fileparse('input/keywords.txt')
    s = zerorpc.Server(Callable())
    s.bind("tcp://127.0.0.1:4242")
    s.run()
