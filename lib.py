import random
import numpy as np
from scipy.stats import norm
import io
from datetime import datetime, timedelta
import math
import pygame

import merc
import events
import army as arm

firstnames = [] # Mercenaries randomly made of
lastnames = []

pikemanImg = pygame.image.load('res/pikeman.png')
cavalryImg = pygame.image.load('res/cavalry.png')
musketeerImg = pygame.image.load('res/musketeer.png')


def bellAge() -> []:
    x = [random.randint(1, 100) for i in range(100)]
    mean = np.mean(x)
    sd = np.std(x)
    pdf = list(map(lambda x: ((x-18) /2) +18, (np.pi*sd) * np.exp(-0.5*((x-mean)/sd)**2)))
    return round(pdf[random.randint(0, 99)])


def readNames():
    with io.open("res/firstnames.txt", mode = "r", encoding = "utf-8") as file:
        global firstnames
        firstnames = file.readlines()
    for i in range(len(firstnames)):
        firstnames[i] = firstnames[i].strip("\n")
       
    with io.open("res/familynames.txt", mode = "r", encoding = "utf-8") as file:
        global lastnames
        lastnames = file.readlines()
    for i in range(len(lastnames)):
        lastnames[i] = lastnames[i].strip("\n")


def oneToTwoSeconds():
    # return random.randint(100, 200) /100
    return random.randint(0, 100) /100


def makeRecruit():
    rec = merc.Merc()
    random.seed()
    rec.firstname = random.choice(firstnames)
    rec.lastname = random.choice(lastnames)
    rec.pay = random.randint(2, 16)
    rec.strength = random.randint(1, 255)
    rec.dexterity = random.randint(1, 255)
    rec.intelligence = random.randint(1, 255)
    rec.charisma = random.randint(1, 255)
    rec.confidence = random.randint(1, 255)
    rec.birthday = events.Event.pointInTime - timedelta(days =365 * bellAge() + random.randint(1, 365))
    # Perks:
    perks = merc.perkList[:]
    if roll(30):
        rec.perks.append(perks.pop(random.randint(0, len(perks)-1)))
    if roll(20):
        rec.perks.append(perks.pop(random.randint(0, len(perks)-1)))
    if roll(10):
        rec.perks.append(perks.pop(random.randint(0, len(perks)-1)))
    
    # for i in range(3): # max 3 perks
    #     prob = random.randint(0, 11) # probability
    #     if i >= prob:
    #         while True: # no duplicates
    #             perk = getRandomPerk()
    #             found = False
    #             for p in rec.perks:
    #                 if p.name == perk.name:
    #                     found = True
    #             if found: continue
    #             rec.perks.append(perk)
    #             break
    return rec

def roll(prob):
    return prob in range(random.randint(1, 100), 100)

def make10Recs():
    mercs = []
    for i in range(10):
        mercs.append(makeRecruit())
    return mercs


def make100Recs():
    return list(map(lambda x:makeRecruit(), range(100)))


def getRandomPerk():
    rand = random.randint(0, len(merc.perkList) -1)
    return merc.perkList[rand]


def getRandomTroopType():
    rand = random.randint(0, 2)
    if rand == 0: return merc.UnitType.pikeman
    if rand == 1: return merc.UnitType.cavalry
    if rand == 2: return merc.UnitType.musketeer


def getRandomPikemen(count):
    pm = []
    for i in range(count):
       rec = makeRecruit()
       rec.xp.typ = merc.UnitType.pikeman
       pm.append(rec)
    return pm
    

def randomArmy(noofSectors, noofTroops):
    army = arm.Army(noofSectors)
    pikemen = []
    cavalryMen = []
    musketeers = []
    for t in range(noofTroops):
        recruit = makeRecruit()
        recruit.xp.typ = getRandomTroopType()
        if recruit.xp.typ == merc.UnitType.pikeman:
            pikemen.append(recruit)
        if recruit.xp.typ == merc.UnitType.cavalry:
            cavalryMen.append(recruit)
        if recruit.xp.typ == merc.UnitType.musketeer:
            musketeers.append(recruit)
    for i,s in enumerate(army.sectors):
        s.pikemen = pikemen[i:math.floor(len(pikemen) /len(army.sectors)) *(i +1)]
        s.cavalryMen = cavalryMen[i:math.floor(len(cavalryMen) /len(army.sectors)) *(i +1)]
        s.musketeers = musketeers[i:math.floor(len(musketeers) /len(army.sectors)) *(i +1)]
    return army


def buildLowArmy(sectors, pikemen = 0, cavalryMen = 0, musketeers = 0):
    p = getRandomPikemen(pikemen)
    army = arm.Army()
    for i in range(sectors):
        army.sectors.append(arm.Sector('Sector ' +str(i), p))
    return army


def countWounds(army: arm.Army):
    w = 0
    for s in army.sectors:
        for p in s.pikemen:
            w += p.wounds
        for p in s.pikemen:
            w += p.wounds
        for p in s.pikemen:
            w += p.wounds
    return w