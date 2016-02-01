# swiss_tour_with_elo
This is a small application that pairs opponent in a swiss type tournament and uses ELO rating system to calculate and update rating of the players after each game.

The application uses
Webapp2 and GoogleAppEngine GQL datastore

This Swiss pairing algorithm chooses players with similar rating in the first rounds (i was confused what should be used here cause there are different variations). Every player plays only once every other player when maximum rounds. Usually swiss pairing tournaments have a number of rounds: log(base2)N where N is the number of players. In this case we play the tournament in maximum rounds with a drawback. Because the algorithms priority is to pair players with similar rating, usually in the last rounds there is NO combination of pairing such that we have the maximum number of tables. In other words in order all players to play against all opponents, some rounds will have fewer tables to play than N/2. Mean also that we will have more than N/2 rounds to finish the tournament.

How to play:
Visitors can view the info of the tournament and logged in users can edit it. Sign up to start playing the tournament.
You can restart the tournament anytime by keeping or deleting the players (rating will not reverted).
You can then add players and finally start the tournament.
On start the pairs of the first round will appear and the next step is to select the results.
The can go to the next round and repeat this process until all players have played each other..
Constrains:
You have to report all matches result in order to continue.
You have to give name and rating to add a player
Some input verifications for username and password
Comments:
With the html/css knowledge i have i think in this part i have done well, i have not used any template for the styles and have written them by myself so the layout result is not that rich.
I have created three Objects in the database: the Users, Players and the Rounds which is the matches between two players. I have not created Tournament database object as the scope was to have one tournament but for bigger implementations it would have been essential.
I have implemented the user registration, authentication and the hashing of password logic.
I have implemented cookie logic.
I have implemented memcache logic to limit db queries and do them only when needed. The Memchache logic i have used is to update memcache on writing to the database so that the next reading is received from memcache and not from DB.
The elo rating algorithm was straightforward
I had the most of the problems, with the swiss pairing algorithm which I have downloaded it and integrated to my application. I have Put it in the lib folder "networkx.

