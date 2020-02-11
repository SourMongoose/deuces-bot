import discord
import random

client = discord.Client()

C = {} # channel dict

def initChannel(ch):
    C[ch] = {}
    C[ch]["started"] = False
    C[ch]["playerMenu"] = False
    
    C[ch]["players"] = []
    C[ch]["autopass"] = []
    
    C[ch]["nPlayers"] = None
    C[ch]["nCards"] = []
    
    C[ch]["deck"] = []
    C[ch]["p1"] = []
    C[ch]["p2"] = []
    C[ch]["p3"] = []
    C[ch]["p4"] = []
    
    C[ch]["pov"] = 0
    C[ch]["hands"] = []
    C[ch]["mid"] = []
    C[ch]["midPlayer"] = None
    C[ch]["winners"] = []

def shuffle(ch):
    global C
    newDeck = []
    while len(C[ch]["deck"]) != 0:
        rm = random.randint(0,len(C[ch]["deck"])-1)
        newDeck.append(C[ch]["deck"][rm])
        C[ch]["deck"] = C[ch]["deck"][:rm] + C[ch]["deck"][rm+1:]
    C[ch]["deck"] = newDeck

def deal(ch):
    if C[ch]["nPlayers"] == 2:
        for i in range(20):
            C[ch]["p1"].append(C[ch]["deck"][i])
            C[ch]["p2"].append(C[ch]["deck"][i+20])
    elif C[ch]["nPlayers"] == 3:
        for i in range(17):
            C[ch]["p1"].append(C[ch]["deck"][i])
            C[ch]["p2"].append(C[ch]["deck"][i+17])
            C[ch]["p3"].append(C[ch]["deck"][i+34])
        C[ch]["p1"].append(C[ch]["deck"][51])
    elif C[ch]["nPlayers"] == 4:
        for i in range(13):
            C[ch]["p1"].append(C[ch]["deck"][i])
            C[ch]["p2"].append(C[ch]["deck"][i+13])
            C[ch]["p3"].append(C[ch]["deck"][i+26])
            C[ch]["p4"].append(C[ch]["deck"][i+39])

value = lambda n: n-2 if n>2 else n+11

comp = lambda a: value(a[0])*100 + a[1]
#comp2 = lambda a: -comp(a)

def sortHands(ch):
    global C
    C[ch]["p1"] = sorted(C[ch]["p1"], key=comp)
    C[ch]["p2"] = sorted(C[ch]["p2"], key=comp)
    C[ch]["p3"] = sorted(C[ch]["p3"], key=comp)
    C[ch]["p4"] = sorted(C[ch]["p4"], key=comp)

@client.event
async def start_(ch):
    global C
    C[ch]["started"] = True
    for i in range(C[ch]["nPlayers"]):
        C[ch]["nCards"].append(0)
    
    C[ch]["deck"] = []
    for i in range(1,5):
        for j in range(1,14):
            C[ch]["deck"].append([j,i])
        
    shuffle(ch)
    deal(ch)
    sortHands(ch)

    for p in ["p1","p2","p3","p4"]:
        C[ch]["hands"].append(C[ch][p])
    
    if C[ch]["nPlayers"] == 2:
        p1Val = value(C[ch]["p1"][0][0])
        p2Val = value(C[ch]["p2"][0][0])
        C[ch]["pov"] = 0 if p1Val<p2Val or (p1Val==p2Val and C[ch]["p1"][0][1]<C[ch]["p2"][0][1]) else 1 
    else:
        for i in range(C[ch]["nPlayers"]):
            if C[ch]["hands"][i][0][0] == 3 and C[ch]["hands"][i][0][1] == 1:
                C[ch]["pov"] = i 
                break
    C[ch]["hands"][C[ch]["pov"]][0] = [3,1]
    
    for i in range(C[ch]["nPlayers"]):
        await sendHand(ch,i)

def reset(ch):
    global C
    
    C[ch]["started"] = False
    C[ch]["gameOver"] = False

    C[ch]["nCards"] = []

    C[ch]["p1"] = []
    C[ch]["p2"] = []
    C[ch]["p3"] = []
    C[ch]["p4"] = []

    C[ch]["pov"] = 0
    C[ch]["hands"] = []
    C[ch]["mid"] = []
    C[ch]["midPlayer"] = -1
    C[ch]["winners"] = []
    
    C[ch]["players"] = []
    C[ch]["autopass"] = []

bomb = lambda h: False if len(h) != 5 else h[0][0]==h[1][0]==h[2][0]==h[3][0] or h[1][0]==h[2][0]==h[3][0]==h[4][0]
fullhouse = lambda h: False if len(h) != 5 else (h[0][0]==h[1][0]==h[2][0] and h[3][0]==h[4][0]) or (h[0][0]==h[1][0] and h[2][0]==h[3][0]==h[4][0])
flush = lambda h: False if len(h) != 5 else h[0][1]==h[1][1]==h[2][1]==h[3][1]==h[4][1]
straight = lambda h: False if len(h) != 5 else h[0][0]%13+1==h[1][0] and h[1][0]%13+1==h[2][0] and h[2][0]%13+1==h[3][0] and h[3][0]%13+1==h[4][0]
triple = lambda h: False if len(h) != 3 else h[0][0]==h[1][0]==h[2][0]
pair = lambda h: False if len(h) != 2 else h[0][0]==h[1][0]

def straights(h):
    o = []
    has = []
    for i in range(13): has.append(False)
    for c in h: has[c[0]-1] = True
    
    for i in range(-11,-2):
        if has[i] and has[i+1] and has[i+2] and has[i+3] and has[i+4]:
            s = []
            for j in range(i,i+4):
                for c in h:
                    if c[0]-1 == (j+13)%13:
                        s.append(c)
                        break
            for c in range(len(h))[::-1]:
                if h[c][0]-1 == (i+17)%13:
                    s.append(h[c])
                    break
            o.append(s)
    
    return o

def flushes(h):
    o = []
    suits = [[],[],[],[],[]]
    for c in h:
        suits[c[1]].append(c)
    
    for s in suits:
        if len(s) > 4:
            for i in range(4,len(s)):
                o.append(s[:4]+[s[i]])
    
    return o

def fullhouses(h):
    o = []
    n = []
    for i in range(14): n.append(0)
    for c in h: n[c[0]] += 1
    
    for i in range(-11,3):
        if n[i] == 3:
            for j in range(-11,3):
                if j != i and 1 < n[j] < 4:
                    tri = []
                    duo = []
                    for c in h:
                        if c[0] == (i+14)%14:
                            tri.append(c)
                        elif c[0] == (j+14)%14:
                            duo.append(c)
                    o.append(tri[:3]+duo[:2])
                    break
    
    return o

def bombs(h):
    o = []
    n = []
    for i in range(14): n.append(0)
    for c in h: n[c[0]] += 1
    
    for i in range(-11,3):
        if n[i] == 4:
            for j in range(-11,3):
                if j != i and 0 < n[j] < 3:
                    quad = []
                    sing = []
                    for c in h:
                        if c[0] == (i+14)%14:
                            quad.append(c)
                        elif c[0] == (j+14)%14:
                            sing.append(c)
                    o.append(quad+sing[:1])
                    break
    
    return o

def handToText(h):
    o = ""
    for c in h: o += toText(c)
    return o

def toText(c):
    return ['','a','2','3','4','5','6','7','8','9','10','j','q','k'][c[0]] + " dchs"[c[1]]

#see if what is played is valid
def check(ch,newMid):
    if len(C[ch]["mid"]) == 0:
        return len(newMid) == 1 or pair(newMid) or triple(newMid) or straight(newMid) or flush(newMid) or fullhouse(newMid) or bomb(newMid)
    elif len(newMid) == 5:
        if bomb(newMid):
            if bomb(C[ch]["mid"]):
                return newMid[2][0] > C[ch]["mid"][2][0]
            else:
                return True
        elif bomb(C[ch]["mid"]):
            return False
        elif straight(newMid) and flush(newMid) and len(C[ch]["mid"]) == 5:
            return not(straight(C[ch]["mid"]) and flush(C[ch]["mid"]) and (value(C[ch]["mid"][4][0]) > value(newMid[4][0]) or (C[ch]["mid"][4][0] == newMid[4][0] and C[ch]["mid"][4][1] > newMid[4][0])))
        elif straight(C[ch]["mid"]) and flush(C[ch]["mid"]):
            return False
        elif fullhouse(newMid):
            return not(fullhouse(C[ch]["mid"]) and value(C[ch]["mid"][2][0]) > value(newMid[2][0]))
        elif fullhouse(C[ch]["mid"]):
            return False
        elif flush(newMid):
            return not(flush(C[ch]["mid"]) and (value(C[ch]["mid"][4][0]) > value(newMid[4][0]) or (C[ch]["mid"][4][0] == newMid[4][0] and C[ch]["mid"][4][1] > newMid[4][1])))
        elif flush(C[ch]["mid"]):
            return False
        elif straight(newMid):
            return not(value(C[ch]["mid"][4][0]) > value(newMid[4][0]) or (C[ch]["mid"][4][0] == newMid[4][0] and C[ch]["mid"][4][1] > newMid[4][1]))
    elif len(newMid) == 3 and len(C[ch]["mid"]) == 3:
        return triple(newMid) and (value(newMid[0][0]) > value(C[ch]["mid"][0][0]) or (newMid[0][0] == C[ch]["mid"][0][0] and newMid[0][1] > C[ch]["mid"][0][1]))
    elif len(newMid) == 2 and len(C[ch]["mid"]) == 2:
        return pair(newMid) and (value(newMid[1][0]) > value(C[ch]["mid"][1][0]) or (newMid[1][0] == C[ch]["mid"][1][0] and newMid[1][1] > C[ch]["mid"][1][1]))
    elif len(newMid) == 1 and len(C[ch]["mid"]) == 1:
        return value(newMid[0][0]) > value(C[ch]["mid"][0][0]) or (newMid[0][0] == C[ch]["mid"][0][0] and newMid[0][1] > C[ch]["mid"][0][1])
    return False

def pass_(ch):
    global C
    if len(C[ch]["mid"]) != 0 or len(C[ch]["hands"][C[ch]["pov"]]) == 0:
        C[ch]["pov"] = (C[ch]["pov"]+1)%C[ch]["nPlayers"]
        if C[ch]["pov"] == C[ch]["midPlayer"]:
            C[ch]["mid"] = []
        if len(C[ch]["hands"][C[ch]["pov"]]) == 0 or C[ch]["players"][C[ch]["pov"]] in C[ch]["autopass"]:
            pass_(ch)

@client.event
async def autoplay(ch):
    global C
    
    if C[ch]["players"][C[ch]["pov"]] != client.user:
        return
    
    s = ""
    hand = C[ch]["hands"][C[ch]["pov"]]
    mid = C[ch]["mid"]
    # play lowest card(s)
    if len(mid) == 0:
        for i in range(len(hand)):
            if hand[i][0] == hand[0][0] or i == 4:
                s += toText(hand[i])
            else:
                break
    # play lowest single possible
    elif len(mid) == 1:
        for i in range(len(hand)):
            if comp(hand[i]) > comp(mid[0]):
                s = toText(hand[i])
                break
    # play lowest double possible
    elif len(mid) == 2:
        for i in range(len(hand)-1):
            if pair([hand[i],hand[i+1]]) and comp(hand[i+1]) > comp(mid[1]):
                s = handToText([hand[i],hand[i+1]])
                break
    # play lowest triple possible
    elif len(mid) == 3:
        for i in range(len(hand)-2):
            if triple([hand[i],hand[i+1],hand[i+2]]) and comp(hand[i+2]) > comp(mid[2]):
                s = handToText([hand[i],hand[i+1],hand[i+2]])
                break
    # five-card hands
    elif len(mid) == 5:
        if bomb(mid):
            for h in bombs(hand):
                if comp(h[2]) > comp(mid[2]):
                    s = handToText(h)
                    break
        elif straight(mid) and flush(mid):
            for h in bombs(hand):
                s = handToText(h)
                break
        elif fullhouse(mid):
            for h in fullhouses(hand):
                if comp(h[2]) > comp(mid[2]):
                    s = handToText(h)
                    break
            if s == "":
                for h in bombs(hand):
                    s = handToText(h)
                    break
        elif flush(mid):
            for h in flushes(hand):
                if comp(h[4]) > comp(mid[4]):
                    s = handToText(h)
                    break
            if s == "":
                for h in fullhouses(hand)+bombs(hand):
                    s = handToText(h)
                    break
        elif straight(mid):
            for h in straights(hand):
                if comp(h[4]) > comp(mid[4]):
                    s = handToText(h)
                    break
            if s == "":
                for h in flushes(hand)+fullhouses(hand)+bombs(hand):
                    s = handToText(h)
                    break

    await play(ch,s)

@client.event
async def play(ch,s):
    global C
    
    try:
        newMid = []
        while len(s):
            n = ""
            while s[0] in "a2345678910jqk":
                n += s[0]
                s = s[1:]
            st = suit2(s[0])
            s = s[1:]
            if [symbol(n),st] in C[ch]["hands"][C[ch]["pov"]]:
                newMid.append([symbol(n),st])
            else:
                return
        
        newMid = sorted(newMid, key=comp)
        
        curr = sum(len(h) for h in C[ch]["hands"])
        currPov = C[ch]["pov"]
        if check(ch,newMid) and (not(C[ch]["hands"][C[ch]["pov"]][0][0] == 3 and C[ch]["hands"][C[ch]["pov"]][0][1] == 1) or (newMid[0][0] == 3 and newMid[0][1] == 1)):
            C[ch]["mid"] = []
            for c in newMid:
                C[ch]["mid"].append(c)
                C[ch]["hands"][C[ch]["pov"]].remove(c)
            C[ch]["midPlayer"] = C[ch]["pov"]
            await sendHand(ch,C[ch]["pov"])
            if len(C[ch]["hands"][C[ch]["pov"]]) == 0:
                C[ch]["winners"].append(C[ch]["pov"])
                if len(C[ch]["winners"]) == C[ch]["nPlayers"]-1:
                    await displayWinners(ch)
                    reset(ch)
            pass_(ch)
        
        if not C[ch]["started"] or sum(len(h) for h in C[ch]["hands"]) != curr:
            await displayMid(ch)
            
            if len(newMid) == 1:
                with open("single.txt", 'a') as fa:
                    fa.write(C[ch]["players"][currPov].id)
            elif len(newMid) == 2:
                with open("double.txt", 'a') as fa:
                    fa.write(C[ch]["players"][currPov].id)
            elif len(newMid) == 3:
                with open("triple.txt", 'a') as fa:
                    fa.write(C[ch]["players"][currPov].id)
            else:
                if bomb(newMid):
                    with open("bomb.txt", 'a') as fa:
                        fa.write(C[ch]["players"][currPov].id)
                elif straight(newMid) and flush(newMid):
                    with open("straightflush.txt", 'a') as fa:
                        fa.write(C[ch]["players"][currPov].id)
                elif fullhouse(newMid):
                    with open("fullhouse.txt", 'a') as fa:
                        fa.write(C[ch]["players"][currPov].id)
                elif flush(newMid):
                    with open("flush.txt", 'a') as fa:
                        fa.write(C[ch]["players"][currPov].id)
                elif straight(newMid):
                    with open("straight.txt", 'a') as fa:
                        fa.write(C[ch]["players"][currPov].id)
    except:
        pass

def symbol(s):
    if s == 'a':
        return 1
    elif s == 'j':
        return 11
    elif s == 'q':
        return 12
    elif s == 'k':
        return 13
    return int(s)
def suit2(s):
    if s == 'd':
        return 1
    elif s == 'c':
        return 2
    elif s == 'h':
        return 3
    elif s == 's':
        return 4
def number(n):
    if n == 1:
        return "A "
    elif n == 11:
        return "J "
    elif n == 12:
        return "Q "
    elif n == 13:
        return "K "
    elif n == 10:
        return "10"
    return str(n)+' '
def suit(n):
    if n == 1:
        return "\U00002666 "
    elif n == 2:
        return "\U00002663 "
    elif n == 3:
        return "\U00002665 "
    elif n == 4:
        return "\U00002660 "
    return "? "

@client.event
async def sendHand(ch,i):
    if C[ch]["players"][i] == client.user:
        return
    
    msg = "```\nYour hand in " + ch.name + ":\n"
    if len(C[ch]["hands"][i]) > 0:
        msg += " __"*len(C[ch]["hands"][i]) + "__\n"
        for c in C[ch]["hands"][i]:
            msg += '|' + number(c[0])
        msg += "  |\n"
        for c in C[ch]["hands"][i]:
            msg += '|' + suit(c[1])
        msg += "  |\n"
        msg += "|  "*len(C[ch]["hands"][i]) + "  |\n"
        msg += "|__"*len(C[ch]["hands"][i]) + "__|\n"
        for c in C[ch]["hands"][i]:
            msg += ['','A','2','3','4','5','6','7','8','9','10','J','Q','K'][c[0]] + ['','d','c','h','s'][c[1]]
        msg += "\n```"
    else:
        msg += "None\n```"
    await client.send_message(C[ch]["players"][i], msg)

@client.event
async def displayMid(ch):
    msg = ""
    for i in range(C[ch]["nPlayers"]):
        if C[ch]["pov"] == i:
            msg += C[ch]["players"][i].mention + " - " + str(len(C[ch]["hands"][i])) + '\n'
        else:
            msg += C[ch]["players"][i].name + " - " + str(len(C[ch]["hands"][i])) + '\n'
    msg += "```\nMiddle card(s):\n"
    if len(C[ch]["mid"]) > 0:
        msg += " __"*len(C[ch]["mid"]) + "__\n"
        for c in C[ch]["mid"]:
            msg += '|' + number(c[0])
        msg += "  |\n"
        for c in C[ch]["mid"]:
            msg += '|' + suit(c[1])
        msg += "  |\n"
        msg += "|  "*len(C[ch]["mid"]) + "  |\n"
        msg += "|__"*len(C[ch]["mid"]) + "__|\n```"
    else:
        msg += "None\n```"
    await client.send_message(ch, msg)
    
    if C[ch]["players"][C[ch]["pov"]] == client.user:
        curr = C[ch]["pov"]
        await autoplay(ch)
        if curr == C[ch]["pov"]:
            pass_(ch)
            await displayMid(ch)

@client.event
async def displayWinners(ch):
    msg = ""
    for i in range(C[ch]["nPlayers"]-1):
        msg += ['\U0001F947','\U0001F948','\U0001F949'][i] + ' ' + C[ch]["players"][C[ch]["winners"][i]].name + '\n'
    msg += "Use `d!start` to start another game!"
    await client.send_message(ch, msg)
    with open("winners.txt", 'a') as fa:
        fa.write(C[ch]["players"][C[ch]["winners"][0]].id)
    with open("players.txt", 'a') as fa:
        for p in C[ch]["players"]:
            fa.write(p.id)

def occur(f, x):
    with open(f, 'r') as fr:
        return fr.read().count(x)

@client.event
async def displayProfile(ch, p):
    w = str(occur("winners.txt", p.id))
    g = str(occur("players.txt", p.id))
    si = str(occur("single.txt", p.id))
    d = str(occur("double.txt", p.id))
    t = str(occur("triple.txt", p.id))
    st = str(occur("straight.txt", p.id))
    fl = str(occur("flush.txt", p.id))
    fh = str(occur("fullhouse.txt", p.id))
    sf = str(occur("straightflush.txt", p.id))
    b = str(occur("bomb.txt", p.id))
    
    msg = "__**" + p.name + "'s Profile:**__\n"
    msg += "You have " + w + " wins in " + g + " games.\n"
    msg += "You have played " + si + " singles, " + d + " doubles, " + t + " triples, " + st + " straights, " + fl + " flushes, " + fh + " full houses, " + sf + " straight flushes, and " + b + " bombs."
    await client.send_message(ch, msg)

@client.event
async def on_ready():
    print("Deuces time!")

'''
 __ __ __ ____
|2 |10|J |A   |
|♥ |♦ |♣ |♠   |
|  |  |  |    |
|__|__|__|____|
2h10dJcAs
'''
@client.event
async def on_message(message):
    global C
    
    msg = message.content.lower()
    ch = message.channel
    au = message.author
    bot = client.user
    
    if ch not in C:
        C[ch] = {}
        initChannel(ch)
    
    if not C[ch]["started"]:
        if msg == "d!help":
            await client.send_message(ch, "Use `d!start` to start a game of deuces, or `d!cancel` to cancel an existing one.\nUse `d!prof` or `d!profile` to access your profile.\nUse `d!addbot` to add a bot to your game, and use `d!rmbot` or `d!removebot` to remove one.")
        elif msg == "d!profile" or msg == "d!prof":
            await displayProfile(ch, au)
        elif msg == "d!start":
            if not C[ch]["playerMenu"]:
                C[ch]["playerMenu"] = True
                C[ch]["players"].append(au)
                await client.send_message(ch, "Use `d!join` to join (and `d!leave` if you have to go)! Once everyone has joined, type `d!start` again to begin.")
                output = str(len(C[ch]["players"])) + "/4 Players:"
                for usr in C[ch]["players"]:
                    output += ' ' + usr.mention
                await client.send_message(ch, output)
            elif 1 < len(C[ch]["players"]) < 5:
                C[ch]["playerMenu"] = False
                C[ch]["nPlayers"] = len(C[ch]["players"])
                await start_(ch)
                await displayMid(ch)
        elif msg == "d!cancel":
            C[ch]["playerMenu"] = False
            C[ch]["players"] = []
            await client.send_message(ch, "Game cancelled!")
        
        if C[ch]["playerMenu"]:
            curr = len(C[ch]["players"])
            if msg == "d!join":
                if au not in C[ch]["players"]:
                    C[ch]["players"].append(au)
            elif msg == "d!leave":
                if au in C[ch]["players"]:
                    C[ch]["players"].remove(au)
            elif msg == "d!addbot":
                C[ch]["players"].append(bot)
            elif msg == "d!rmbot" or msg == "d!removebot":
                if bot in C[ch]["players"]:
                    C[ch]["players"].remove(bot)
            if curr != len(C[ch]["players"]):
                output = str(len(C[ch]["players"])) + "/4 Players:"
                for usr in C[ch]["players"]:
                    output += ' ' + usr.mention
                await client.send_message(ch, output)
    else:
        if msg == "d!help":
            await client.send_message(ch, "If it's your turn, type the cards you want to play (e.g. `3D3H` for 3\U00002666 3\U00002665) or type `pass` to pass.\nUse `d!display` to re-display the current hand, and use `d!leave` or `d!forfeit` to leave an ongoing game.")
        elif msg == "d!profile" or msg == "d!prof":
            await displayProfile(ch, au)
        if au in C[ch]["players"]:
            if au == C[ch]["players"][C[ch]["pov"]]:
                if msg == "pass":
                    curr = C[ch]["pov"]
                    pass_(ch)
                    if C[ch]["pov"] != curr:
                        await displayMid(ch)
                else:
                    await play(ch,msg)
            if msg == "d!display":
                await displayMid(ch)
            elif msg == "d!leave" or msg == "d!forfeit":
                if au not in C[ch]["autopass"]:
                    C[ch]["autopass"].append(au)
                    if len(C[ch]["autopass"]) == len(C[ch]["nPlayers"]):
                        reset(ch)
            elif msg == "d!reset":
                reset(ch)
                await client.send_message(ch, "Game reset!")
            
client.run('INSERT TOKEN HERE')
