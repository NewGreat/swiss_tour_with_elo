__author__ = 'user01'
import random
import math
import networkx as nx

winPoints = 1
drawPoints = 0.5
byePoints = 0
dbg = False


class Tournament(object):

    def __init__(self, playersDict={}):
        self.playersDict = playersDict
        self.pointLists = {}
        self.pointTotals =[]
        self.tablesOut = []
        self.startingTable = 1
        self.MaxGroup = 50
        self.currentRound = 0
        self.bye_player = None

    def addPlayer( self, IDNumber, playerName, rating , fixedSeating=False ):

        '''
        Holds player data that are in the event.

        Each player entry is a dictonary named by ID#

        ID : { Name:String,
                Opponents:List, Each entry is a ID number of someone you played
                Results:List, Each entry is a list of wins-losses-draws for the round
                Points:Int}}
        '''

        self.playersDict[IDNumber] = {  "Name": playerName,
                                        "Opponents":[],
                                        "Results":[],
                                        "Rating":rating}

    def pairRound(self):
        """
        Process overview:
            1.) Create lists of players with each point value

            2.) Create a list of all current points and sort from highest to lowest

            3.) Loop through each list of points and assign players opponents based with same points

            4.) Check for left over players and assign a pair down
        """
        if not len(self.tablesOut):
            self.currentRound += 1

            #Clear old round pairings
            self.roundPairings = {}
            self.openTable = self.startingTable

            #Contains lists of players sorted by how many points they currently have
            self.pointLists = pointLists = {}

            #Contains a list of points in the event from high to low
            self.pointTotals = pointTotals = []

            #Counts our groupings for each point amount
            self.countPoints = {}


            #Add all players to pointLists
            for player in self.playersDict:
                info = self.playersDict[player]
                #If this point amount isn't in the list, add it
                if "%s_1"%info['Rating'] not in pointLists:
                    pointLists["%s_1"%info['Rating']] = []
                    self.countPoints[info['Rating']] = 1

                #Breakers the players into groups of their current points up to the max group allowed.
                #Smaller groups mean faster calculations
                if len(pointLists["%s_%s"%(info['Rating'], self.countPoints[info['Rating']])]) > self.MaxGroup:
                    self.countPoints[info['Rating']] += 1
                    pointLists["%s_%s"%(info['Rating'], self.countPoints[info['Rating']])] = []

                #Add our player to the correct group
                pointLists["%s_%s"%(info['Rating'], self.countPoints[info['Rating']])].append(player)

            #Add all points in use to pointTotals
            for points in pointLists:
                pointTotals.append(points)

                #Randomize the players in the list so the first player isn't always the first paired
                random.shuffle(pointLists[points])

            #Sort our point groups based on points
            pointTotals.sort(reverse=True, key=lambda s: int(s.split('_')[0]))

            printdbg( "Point toals after sorting high to low are: %s"%pointTotals, 3 )

            #Actually pair the players utilizing graph theory networkx
            for points in pointTotals:
                printdbg( points, 5 )

                #Create the graph object and add all players to it
                bracketGraph = nx.Graph()
                bracketGraph.add_nodes_from(pointLists[points])

                printdbg( pointLists[points], 5 )
                printdbg( bracketGraph.nodes(), 5 )

                #Create edges between all players in the graph who haven't already played
                for player in bracketGraph.nodes():
                    for opponent in bracketGraph.nodes():
                        if opponent not in self.playersDict[player]["Opponents"] and player != opponent:
                            #Weight 1 is the default, if a person has more points, give higher weight to make sure they get paired this time
                            wgt = 10
                            if self.playersDict[player]["Rating"] > points or self.playersDict[opponent]["Rating"] > points:
                                wgt = 2
                            #Create edge
                            bracketGraph.add_edge(player, opponent, weight=wgt)

                #Generate pairings from the created graph
                pairings = nx.max_weight_matching(bracketGraph)

                printdbg( pairings, 3 )

                #Actually pair the players based on the matching we found
                for p in pairings:
                    if p in pointLists[points]:
                        self.pairPlayers(p, pairings[p])
                        pointLists[points].remove(p)
                        pointLists[points].remove(pairings[p])

                #Check if we have an odd man out that we need to pair down
                if len(pointLists[points]) > 0:
                    #Check to make sure we aren't at the last player in the event
                    printdbg(  "Player %s left in %s. The index is %s and the length of totals is %s"%(pointLists[points][0], points, pointTotals.index(points), len(pointTotals)), 3)
                    if pointTotals.index(points) + 1 == len(pointTotals):
                        while len(pointLists[points]) > 0:
                            #If they are the last player give them a bye
                            self.assignBye(pointLists[points].pop(0))
                    else:
                        #Add our player to the next point group down
                        nextPoints = pointTotals[pointTotals.index(points) + 1]

                        while len(pointLists[points]) > 0:
                            pointLists[nextPoints].append(pointLists[points].pop(0))

            #Reassign players with fixed seating needs
            openTables = []
            displacedMatches = []

            #Create a copy of the pairings so we can edit the pairings during the loop
            clonePairings = self.roundPairings.copy()

            for table in clonePairings:
                p1 = self.roundPairings[table][0]
                p2 = self.roundPairings[table][1]


            #Assign players displaced by a fixed seating to new tables
            for match in displacedMatches:
                if len(openTables):
                    self.roundPairings[openTables[0]] = match
                    del(openTables[0])
                else:
                    self.pairPlayers(match[0], match[1])

            #If there are open tables still, remove them from the matches out
            for table in openTables:
                self.tablesOut.remove(table)

            # #Return the pairings for this round
            return self.roundPairings
        else:
            #If there are still tables out and we haven't had a forced pairing, return the tables still "playing"
            return self.tablesOut

    def pairPlayers( self, p1, p2 ):
        printdbg("Pairing players %s and %s"%(p1, p2), 5)

        self.playersDict[p1]["Opponents"].append(p2)
        self.playersDict[p2]["Opponents"].append(p1)

        self.roundPairings[self.openTable] = [p1, p2]
        self.tablesOut.append(self.openTable)

        self.openTable += 1

    def assignBye( self, p1, reason="bye" ):
        printdbg( "%s got the bye"%p1, 2)
        self.bye_player = p1
        self.playersDict[p1]["Results"].append([0,0,0])

        self.playersDict[p1]["Opponents"].append(0)

        #Add points for "winning"
        self.playersDict[p1]["Rating"] += byePoints

    def reportMatch( self, table, result ):
        #table is an integer of the table number, result is a list
        p1 = self.roundPairings[table][0]
        p2 = self.roundPairings[table][1]
        otresult =[]
        if result[2] == 1:
            #If values are the same they drew! Give'em each a point
            new_rates = calculate_elo_rating(self.playersDict[p1]["Rating"], self.playersDict[p2]["Rating"], 0.5)
            self.playersDict[p1]["Rating"] = int(round(new_rates[0]))
            self.playersDict[p2]["Rating"] = int(round(new_rates[1]))
            otresult = [0, 0, 1]
        else:
            #Figure out who won and assing points
            if result[0] > result[1]:
                new_rates = calculate_elo_rating(self.playersDict[p1]["Rating"], self.playersDict[p2]["Rating"])
                self.playersDict[p1]["Rating"] = int(round(new_rates[0]))
                self.playersDict[p2]["Rating"] = int(round(new_rates[1]))
            elif result[1] > result[0]:
                new_rates = calculate_elo_rating(self.playersDict[p2]["Rating"], self.playersDict[p1]["Rating"])
                self.playersDict[p2]["Rating"] = int(round(new_rates[0]))
                self.playersDict[p1]["Rating"] = int(round(new_rates[1]))
            otresult = [result[1], result[0], 0]
        printdbg("Adding result %s for player %s"%(result, p1), 3)
        self.playersDict[p1]["Results"].append(result)

        printdbg("Adding result %s for player %s"%(otresult, p2), 3)
        self.playersDict[p2]["Results"].append(otresult)

        #Remove table reported from open tables
        self.tablesOut.remove(table)

    def report_all(self, pairings, resultList):
        self.roundPairings = pairings
        self.tablesOut = pairings.keys()
        keys = list(self.tablesOut)
        for idx in range(len(resultList)):
            if resultList[idx] == "Player1":
                self.reportMatch(keys[idx], [1, 0, 0])
            elif resultList[idx] == "Player2":
                self.reportMatch(keys[idx], [0, 1, 0])
            elif resultList[idx] == "Draw":
                self.reportMatch(keys[idx], [0, 0, 1])



def calculate_elo_rating(p1_r, p2_r, p1_score=1.0):
    Qa = math.pow(10, (p1_r / 400.0))
    Qb = math.pow(10, (p2_r / 400.0))
    EA = Qa / (Qa + Qb)
    EB = Qb / (Qa + Qb)
    new_p1_r = round(p1_r + (k_factor(p1_r) * (p1_score - EA)))
    new_p2_r = round(p2_r + (k_factor(p2_r) * (1 - p1_score - EB)))
    return (new_p1_r, new_p2_r)


def k_factor(p_rating):
    if p_rating < 2100:
        k = 32
    elif (p_rating >= 2100) and (p_rating < 2400):
        k = 24
    else:
        k = 16
    return k

def printdbg( msg, level=1 ):
    if dbg == True:
        print msg


