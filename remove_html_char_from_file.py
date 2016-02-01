__author__ = 'user01'

import sys



if __name__ == "__main__":
    startstring = sys.argv[1]
    s_occurance = int(sys.argv[2])

    endstring = sys.argv[3]
    e_occurance = int(sys.argv[4])
    file = sys.argv[5]


startfound = 0
endfound = 0
with open(file,'r') as f:
    newlines = []
    for line in f.readlines():
        if line.find(endstring) != -1:
            endfound += 1
            #print line
        if startfound!=s_occurance or endfound==e_occurance:
            newlines.append(line)
        elif startfound==s_occurance and endfound!=e_occurance:
            newlines.append(line.replace('<', '&lt').replace('>', '&gt').replace('&','&amp').replace('"', '&quot').replace("'",'&apos'))
        if line.find(startstring) != -1:
            startfound += 1
            #print line

with open(file, 'w') as f:
    for line in newlines:
        f.write(line)