from multiprocessing import Process
import sys, pygame
import locale
from threading import Lock
import itertools
import random

import lib
import gameenv
import text
import layout
import section
from sections import header
import item
import events
import merc
from sections.assignment import AssignmentSection
from sections.troops import TroopsSection
import sections.actions as actions
from sections.camp import CampSection
from sections.recruitment import RecruitmentSection
from army import Army
from assignments import Assignment
import scenarios
import battlefield

assignm = 0
troops = 1
camp = 2
recruitment = 3


class Game(Process):
	# static fields
	env: gameenv.GameEnv
	running: True
	screen = None # pygame screen
	sections = [] # columns on the playfield
	focusedSection = None # cursor is in this column
	focusedSectionIndex = None
	
	recruits = [] # all available recruits
	mercs = [] # all recruited mercenaries
	army = Army()
	assignment = None
	battlefield: battlefield.Battlefield
	
	lock = Lock()
	
	def __init__(self, env: gameenv.GameEnv):
		super().__init__()
		locale.setlocale(locale.LC_TIME, "de_DE")
		self.env = env
		self.running = True
		
		lib.readNames()
	
		self.background = pygame.image.load('res/alu.jpg')
		
		pygame.init()
		
		# pygame.key.set_repeat(250, 60)
		size = env.width, env.height
		
		self.screen = pygame.display.set_mode(size)
		text.Text.screen = self.screen
		section.Section.screen = self.screen
		item.Item.screen = self.screen
		section.SectionStats.screen = self.screen
		section.ScrollBar.screen = self.screen
		
		mainLayout = layout.Layout(self.env.width, self.env.height)
		self.header = header.Header(mainLayout.getHeader(), self)
		self.sections.append(AssignmentSection(mainLayout.getColumn(0), self))
		self.border = section.Section(mainLayout.getColumn(1), self)
		self.sections.append(TroopsSection(mainLayout.getColumn(2), self))
		self.actions = actions.ActionsSection(mainLayout.getColumn(3), self)
		self.sections.append(CampSection(mainLayout.getColumn(4), self))
		self.sections.append(RecruitmentSection(mainLayout.getColumn(5), self))
		
		self.focusedSection = self.sections[recruitment]
		self.focusedSectionIndex = recruitment
		self.focusedSection.focus()
		
		self.gameEvents = events.Events()
		# self.gameEvents.addEvent(events.Event(events.CLOCK_SECONDS, 1, self.gameEvents.currentTime))
		# self.gameEvents.addEvent(events.Event(events.NEW_RECRUITS_EVENT, 1))
	
	def start(self):
		clock = pygame.time.Clock()
		self.mercs = lib.make10Recs()
		self.sections[camp].update(self.mercs)
		while self.running:
			# evaluate player action
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
					exit()
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_g: # UP
						focus = self.focusedSection.keyUp()
						self.actions.activeItemChanged(focus)
						
					elif event.key == pygame.K_r: # DOWN
						focus = self.focusedSection.keyDown()
						self.actions.activeItemChanged(focus)
						
					elif event.key == pygame.K_n: # LEFT
						if self.focusedSectionIndex >0:
							self.focusedSectionIndex -= 1
							self.focusedSection = self.sections[self.focusedSectionIndex]
							for s in self.sections: s.unfocus()
							focus = self.focusedSection.focus()
							self.actions.activeItemChanged(focus)
							
					elif event.key == pygame.K_t: # RIGHT
						if self.focusedSectionIndex <len(self.sections) -1:
							self.focusedSectionIndex += 1
							self.focusedSection = self.sections[self.focusedSectionIndex]
							for s in self.sections: s.unfocus()
							focus = self.focusedSection.focus()
							self.actions.activeItemChanged(focus)
							
					elif event.key == pygame.K_SPACE: # SPACE
						selection = self.focusedSection.space()
						if len(selection) >0:
							self.actions.selectionActive(selection)
							
					elif event.key == pygame.K_TAB or event.key == pygame.K_s: # TAB
						self.actions.tab()
						
					elif event.key == pygame.K_l:
						self.actions.up()
					elif event.key == pygame.K_a:
						self.actions.down()
						
					elif event.key == pygame.K_RETURN or event.key == pygame.K_h: # RETURN
						if self.actions.activeItem == None:
							self.actions.act(self.actions.selectedAction)
						else:
							self.focusedSection.act(self.actions.selectedAction)
						
					elif event.key == pygame.K_ESCAPE: # ESCAPE
						self.actions.activeItemChanged(None)
					
			# evaluate game events
			for e in self.gameEvents.getRaisedEvents():
				if e.name == events.CLOCK_SECONDS:
					self.gameEvents.renew(e, 1, self.gameEvents.currentTime)
					self.header.updateClock(self.gameEvents.currentTime.strftime("%A, %d. %B %Y - %H:%M:%S"))
					
				elif e.name == events.NEW_RECRUITS_EVENT:
					# self.gameEvents.renew(e, 10)
					self.recruits.append(lib.makeRecruit())
					self.sections[recruitment].update(self.recruits)
					# self.gameEvents.renew(e, 1)
				
				elif e.name == events.BATTLE_EVENT:
					# if self.checkSurrender():
					# 	self.gameEvents.remove(e)
					# else:
					# 	self.matchup()
					# 	e.renew(0.1)
					# self.conflict()
					# e.renew(1)
					pass
				
				elif e.name == events.COMBAT_EVENT:
					result = self.rollFight(e.payload[0], e.payload[1])
					if result == True: # fight still going
						e.renew(lib.oneToTwoSeconds())
						pass
					elif result.__class__.__name__ == 'tuple': # new pair
						self.gameEvents.remove(e)
						self.gameEvents.addEvent(events.Event(events.COMBAT_EVENT, lib.oneToTwoSeconds(), (result, e.payload[1])))
					else: # fight settled
						arm, enemy = self.battlefield.getArmies()
						self.sections[troops].update(arm)
						self.assignment.army = enemy
						self.sections[assignm].setAssignment(self.assignment)
						self.gameEvents.remove(e)
					# self.sections[troops].flash(e.payload[2], result[0])
					# self.sections[assignment].flash(e.payload[2], result[1])
					
					
			# draw frame
			self.screen.blit(self.background, pygame.Rect(0, 0, 0, 0))
			self.header.draw()
			self.border.draw()
			self.actions.draw()
			for s in self.sections:
				s.draw()
			
			pygame.display.flip()
			dt = clock.tick(30)
			self.header.updateFps(str(dt))
			self.gameEvents.update(dt) # update game's current time

	def exit(self):
		self.running = False
		pygame.quit()
		sys.exit()
		
	# --- callbacks ---
	
	def doRecruit(self, recruit: merc.Merc):
		# self.lock.acquire()
		# try:
		self.recruits.remove(recruit) # throws 'not in list'
		self.mercs.append(recruit)
		self.gameEvents.addEvent(events.Event(events.RECRUITED_EVENT, 0.001))
		self.sections[recruitment].update(self.recruits)
		self.sections[camp].update(self.mercs)
		# except:
		# 	pass
		# self.lock.release()
	
	def doRecruitSelected(self, recruits):
		"""Called from recruitment when selection is accepted"""
		print(recruits)
	
	def doTrain(self, merc:merc.Merc, typ:merc.UnitType):
		merc.xp.typ = typ
		self.sections[camp].update(self.mercs)
	
	def selectThisAssignment(self, assign:Assignment):
		self.army = Army(assign.sectors)
		self.assignment = assign
		self.sections[troops].update(self.army)
		# build enemy troops:
		army = lib.buildLowArmy(1, 10)
		assign.army = army
		self.sections[assignm].setAssignment(assign)
		
		
	def battle(self):
		self.battlefield = battlefield.Battlefield(self.army, self.assignment.army)
		# self.gameEvents.addEvent(events.Event(events.BATTLE_EVENT, 1))
		self.conflict()
		
	def conflict(self):
		for s in self.battlefield.sectors:
			pikemen = s.conflicPikemen()
			if pikemen:
				for p in pikemen:
					self.gameEvents.addEvent(events.Event(events.COMBAT_EVENT, lib.oneToTwoSeconds(), (p, s)))
			cavalryMen = s.conflictCavalryMen()
			if cavalryMen:
				for c in cavalryMen:
					self.gameEvents.addEvent(events.Event(events.COMBAT_EVENT, lib.oneToTwoSeconds(), (c, s)))
			musketeers = s.conflictMusketeers()
			if musketeers:
				for m in musketeers:
					self.gameEvents.addEvent(events.Event(events.COMBAT_EVENT, lib.oneToTwoSeconds(), (m, s)))
			
	
	def rollFight(self, pair, sector):
		merc = pair[0]
		enem = pair[1]
		powMerc = merc.getPower()
		powEnem = enem.getPower()
		powMerc *= merc.getAdvantage(enem.xp.typ) *100 # make int
		powEnem *= merc.getAdvantage(merc.xp.typ) *100
		powMerc *= int((1/ (merc.wounds +2)) *10)
		powEnem *= int((1/ (merc.wounds +2)) *10)
		hitMerc = random.randint(0, powMerc) //powEnem
		hitEnem = random.randint(0, powEnem) //powMerc
		
		merc.wounds += hitEnem
		enem.wounds += hitMerc
		
		kia = False
		if merc.wounds >=4:
			merc.wounds = 4
			kia = True
		if enem.wounds >=4:
			enem.wounds = 4
			kia = True
		if kia:
			newPair = sector.kia(pair)
			if newPair:
				return newPair
			return False
		return True
		
	
	def checkSurrender(self):
		# count wounds
		troops = lib.countWounds(self.army)
		enemy = lib.countWounds(self.assignment.army)
		troopsLen = len(self.assignment.army.getTotalMercs())
		enemyLen = len(self.assignment.army.getTotalMercs())
		if troops //2 > troopsLen and enemy //2 <=enemyLen: # enemy won
			return troops
		elif enemy //2 > enemyLen and troops //2 <=troopsLen: # troops won
			return enemy
		elif troops == troopsLen *4 and enemy < enemyLen *4: # all troops dead
			return troops
		elif enemy == enemyLen *4 and troops < troopsLen *4: # all enemy dead
			return enemy
		else: return None # all dead?
		
	def put10Pikemen(self, sectorIndex):
		move = []
		for m in self.mercs:
			if m.xp.typ == merc.UnitType.pikeman:
				move.append(m)
			if len(move) == 10: break
		for m in move:
			self.army.sectors[sectorIndex].pikemen.append(m)
			self.mercs.remove(m)
		self.sections[troops].update(self.army)
		self.sections[camp].update(self.mercs)
		# update info changes:
		self.actions.activeItemChanged(self.sections[troops].items[self.sections[troops].itemFocusIndex])
		
	def put10CavalryMen(self, sectorIndex):
		pass
		
	def put10Musketeers(self, sectorIndex):
		pass
		
	def removeAll(self, sectorIndex):
		pass
		
	# --- game menu ---
	
	def quit(self):
		exit()
	
	# --- test ---

	def doMake100Recruits(self):
		self.recruits.extend(lib.make100Recs())
	
	def initPfullingScenario(self):
		scene = scenarios.PfullingScenario()
		self.army = scene.army
		self.assignment = scene.assignment
		self.sections[assignm].setAssignment(scene.assignment)
		self.sections[troops].update(scene.army)

env = gameenv.GameEnv()
game = Game(env)
game.start()
