#!/usr/bin/env python

## xChat G15 Highlighter Plugin.
## This plugin is for xChat under Linux only. There are other plugins for Windows.
## You need G15Tools installed. See http://g15tools.sourceforge.net/ - You also need xChat. See http://www.xchat.org/
## You need to be able to see a clock on your LCD, and have write access to the path you choose in the config file.
## This script now starts G15Composer listening on the right path unless you set it not to in the config. It will also kill it upon an unload.
## Also added is '/clearlcd', which clears back to the startup screen.
## This is licenced under the GPL V3.0, which should be included in the archive as 'LICENCE' - if it is for any reason not, please see http://www.gnu.org/licenses/gpl.txt
## This was written by Lattyware (Gareth Latty)
## Enjoy use of this script. I am not liable for anything that happens from the use of it.
## V2.6 implements a few bug-fixes (mainly the query error bug, and the timing bug), as well as the new animation system and the option to clear after highlight (disabled in default config)
## V2.5 adds lots of new features, like LCD backlight flashing (really grabs your attention!), M key lighting (more subtle), and some other more minor things.
## V2.0 is much, much better than the origonal. It uses pipes properly, fixes some critical bugs, and is a lot better in every way due to the fact the actual python it is made in is a lot cleaner and nicer to use. It also has a proper config file ('<xchat directory>/HG15/config.txt'). The config allows full customisation of what is sent to the screen, with a number of variables.

import xchat
import os
import signal 
import thread
from subprocess import Popen, PIPE
from time import localtime, strftime, sleep
from ConfigParser import RawConfigParser

__module_name__ = "xChat G15 Highlighter Plugin" 
__module_version__ = "2.6" 
__module_description__ = "A script to display highlights in xChat on your G15 screen, By Lattyware." 
module_dir = xchat.get_info("xchatdir") + "/G15H/" # (Not Official xChat stuff, but fits in nicely)

def writetolog(message):
	debuglog = open(module_dir + "log.txt","a")
	debuglog.write(message + "\n")
	debuglog.close

DEBUG = False

if (DEBUG == True): 
	debuglog = open(module_dir + "log.txt","w")
	debuglog.close
	writetolog("Debug Log Started")

class preferences:
	config = []
	parse = None
	lcdconnection = None
	
	def __init__(self):
		if (DEBUG == True): 
			self.writetolog("Init Prefs")
		self.loadprefs(None, None, None)
		if (DEBUG == True): 
			self.writetolog("Done")
			
	def loadprefs(self, word, word_eol, userdata):
		if (self.lcdconnection != None):
			self.lcdconnection.offlights(None, None, None)
		prefs = open(module_dir + "config.txt")
		self.parse = RawConfigParser()
		self.parse.readfp(prefs)
		prefs.close()
		print "Prefrences Loaded"
				
	def value(self,option):
		if (DEBUG == True): 
			self.writetolog("Prefs -> Value") 
		return self.parse.get("config",option)
		if (DEBUG == True): 
			self.writetolog("Done")
			
	def floatvalue(self,option):
		if (DEBUG == True): 
			self.writetolog("Prefs -> FloatValue") 
		return self.parse.getfloat("config",option)
		if (DEBUG == True): 
			self.writetolog("Done")
	
	def intvalue(self,option):
		if (DEBUG == True): 
			self.writetolog("Prefs -> IntValue") 
		return self.parse.getint("config",option)
		if (DEBUG == True): 
			self.writetolog("Done")
			
	def boolvalue(self,option):
		if (DEBUG == True): 
			self.writetolog("Prefs -> IntValue") 
		return self.parse.getboolean("config",option)
		if (DEBUG == True): 
			self.writetolog("Done")
			
	def writetolog(self, message):
		debuglog = open(module_dir + "log.txt","a")
		debuglog.write(message + "\n")
		debuglog.close

class lcdconnection:
	composer = None
	pipe = None
	prefs = None
	checker=None
	
	def __init__(self, prefs):
		self.prefs = prefs
		self.prefs.lcdconnection = self
		if (DEBUG == True): 
			self.writetolog("Init LCDConnection")
		if (os.access(prefs.value("path"),os.F_OK)):
			os.unlink(prefs.value("path"))
		os.mkfifo(prefs.value("path"))
		if (prefs.boolvalue("start") == True):
			self.composer = Popen("g15composer " + prefs.value("path"), shell=True)
		signal.signal(signal.SIGALRM, self.errorhandle)
		signal.alarm(5)
		self.pipe = os.open(prefs.value("path"), os.O_WRONLY)
		signal.alarm(0) 
		self.clearscreen(None, None, None)
		if (DEBUG == True): 
			self.writetolog("Done")
		
	def composerPID(self):
		if (DEBUG == True): 
			self.writetolog("lcdcon->g15composerpid")
		return self.composer.pid+1
		if (DEBUG == True): 
			self.writetolog("Done")
		
	def sendmessage(self, message):
		if (DEBUG == True): 
			self.writetolog("lcdcon->sendmessage")
		os.write(self.pipe,message)		
		if (DEBUG == True): 
			self.writetolog("Done")
			
	def setlights(self, mode):
		self.sendmessage("KM " + self.prefs.value("lights") + " " + mode + "\n")
		
	def offlights(self, word, word_eol, userdata):	#Yes, this is pointless. It's just easiest with the hook.
		self.setlights("0")
		
	def clearscreen(self, word, word_eol, userdata):
		if (DEBUG == True): 
			self.writetolog("lcdcon->clearscreen")
		version="V" + str(__module_version__)
		if (self.prefs.value("clearmode").lower() == "text"):
			self.sendmessage('PC 0\nTL \"' + "G15 Highlighter".ljust(20) + '\" \"' + "Script For xChat".center(20) + '\" \"' + "By Lattyware".rjust(20) + '\" \"\" \"' + version.center(20) + '\"\nPR 0 30 160 40\n')
		elif (self.prefs.value("clearmode").lower() == "image"):
			if (self.prefs.value("clearimage").lower() == "currentversion"):
				self.sendmessage('PC 0\nWS \"' + module_dir + __module_version__ +'.wbmp\"\n')
			else:
				self.sendmessage('PC 0\nWS \"' + module_dir + self.prefs.value("clearimage") +'.wbmp\"\n')
		elif (self.prefs.value("clearmode").lower() == "blank"):
			self.sendmessage('PC 0\n')
		elif (self.prefs.value("clearmode").lower() == "animation"):
			if (self.prefs.value("clearanimation").lower() == "currentversion"):
				frames=[__module_version__ + "/frame0",__module_version__ + "/frame1",__module_version__ + "/frame2",__module_version__ + "/frame3",__module_version__ + "/frame4",__module_version__ + "/frame5",__module_version__ + "/frame6"]
				thread.start_new_thread(self.animate,(self.prefs.floatvalue("clearanimationspeed"),frames))
			else:
				thread.start_new_thread(self.animate,(self.prefs.floatvalue("clearanimationspeed"),self.prefs.value("clearanimation").split(",")))
		print "LCD Cleared."
		if (DEBUG == True): 
			self.writetolog("Done")
		
	def writetolog(self, message):
		debuglog = open(module_dir + "log.txt","a")
		debuglog.write(message + "\n")
		debuglog.close
		
	def errorhandle(self, signum, frame):
		raise IOError, "Couldn't open!"
		
	def flashbacklight(self, times, timewait, level1, level2):
		for i in range(times):
			self.sendmessage("LB " + level1 + "\n")
			sleep(timewait)
			self.sendmessage("LB " + level2 + "\n")
			sleep(timewait)
		
	def timeroff(self, time, another):
		sleep(time)
		self.setlights("0")
		
	def timedclear(self, time, another):
		sleep(time)
		self.clearscreen(None, None, None)
		
	def animate(self, time, frames):
		for i in frames:
			sleep(time)
			self.sendmessage('PC 0\nWS \"' + module_dir + i +'.wbmp\"\n')
		
class checker:
	highlights = []
	prefs = None
	lcd = None
	optionname = ["%message%","%messagewrapped%","%newline%","%channel%","%textheight%","%textsize%","%time%","%nick%","%hours%","%minutes%","%seconds%"] 
	
	def __init__(self, prefs, lcd):
		if (DEBUG == True): 
			self.writetolog("Init checker")
		if (xchat.get_prefs("irc_extra_hilight")):
			self.highlights = xchat.get_prefs("irc_extra_hilight").split(',')
		if (xchat.get_prefs("irc_nick1")):
			self.highlights.append(xchat.get_prefs("irc_nick1"))
		if (xchat.get_prefs("irc_nick2")):
			self.highlights.append(xchat.get_prefs("irc_nick2"))
		if (xchat.get_prefs("irc_nick3")):
			self.highlights.append(xchat.get_prefs("irc_nick3"))
		self.prefs = prefs
		self.lcd = lcd
		self.lcd.checker = self
		if (DEBUG == True): 
			self.writetolog("Done")
		
	def check(self, word, word_eol, userdata):
		if (DEBUG == True): 
			self.writetolog("checker->Check")
		message = word_eol[3].replace(":","",1)
		if (message.startswith("+")):
			message = message.replace("+","",1)
		if (message.startswith("-")):
			message = message.replace("-","",1)
		nick = word[0].split("!")[0].split(":")[1]
		channel = word[2]
		messagewrapped = message
		pieces = []
		width = self.prefs.value("screenwidth")
		for i in xrange(0, len(messagewrapped), int(width)): pieces.append(messagewrapped[i:i+int(width)])
		messagewrapped = '\" \"'.join(pieces)
		time = strftime("%H:%M:%S", localtime())
		hours = strftime("%H", localtime())
		minutes = strftime("%M", localtime())
		seconds = strftime("%S", localtime())
		textheight = self.prefs.value("height")
		textsize = self.prefs.value("size")
		self.optionvalue = [message,messagewrapped,"\n",channel,textheight,textsize,time,nick,hours,minutes,seconds]
		a = 0
		tosend = self.prefs.value("string")
		for i in self.highlights:
			if (self.prefs.boolvalue("query") == True):
				if (channel.lower() == i.lower()):
					for i in self.optionname:
						tosend = tosend.replace(i.lower(),self.optionvalue[a])
						a = a + 1
					self.lcd.sendmessage(tosend)
					if (self.prefs.boolvalue("clearafterhighlight") == True):
						thread.start_new_thread(self.lcd.timedclear,(self.prefs.floatvalue("clearafterhighlighttime"),None))
					if (self.prefs.boolvalue("backlight") == True):
						thread.start_new_thread(self.lcd.flashbacklight,(self.prefs.intvalue("backlightnumber"),self.prefs.floatvalue("backlightwait"),self.prefs.value("backlightlevel1"),self.prefs.value("backlightlevel2")))
					self.lcd.setlights("1")
					thread.start_new_thread(self.lcd.timeroff,(self.prefs.floatvalue("lighttime"),None))
					if (DEBUG == True): 
						self.writetolog("Done")
					return xchat.EAT_NONE 
			if (word_eol[3].lower().find(i.lower()) != -1):
				for i in self.optionname:
					tosend = tosend.replace(i,self.optionvalue[a])
					a = a + 1
				self.lcd.sendmessage(tosend)
				if (self.prefs.boolvalue("clearafterhighlight") == True):
					thread.start_new_thread(self.lcd.timedclear,(self.prefs.floatvalue("clearafterhighlighttime"),None))
				if (self.prefs.boolvalue("backlight") == True):
					thread.start_new_thread(self.lcd.flashbacklight,(self.prefs.floatvalue("backlightnumber"),self.prefs.floatvalue("backlightwait"),self.prefs.value("backlightlevel1"),self.prefs.value("backlightlevel2")))
				self.lcd.setlights("1")
				thread.start_new_thread(self.lcd.timeroff,(self.prefs.intvalue("lighttime"),None))
				if (DEBUG == True): 
					self.writetolog("Done")
				return xchat.EAT_NONE
		if (DEBUG == True): 
			self.writetolog("Done")
	
	def writetolog(self, message):
		debuglog = open(module_dir + "log.txt","a")
		debuglog.write(message + "\n")
		debuglog.close
				
class unloader:
	lcd = None
	prefs = None
	
	def __init__(self, prefs, lcd):
		if (DEBUG == True): 
			self.writetolog("Init unloader")
		self.lcd = lcd
		self.prefs = prefs
		if (DEBUG == True): 
			self.writetolog("Done")
	
	def unload(self,userdata):
		if (DEBUG == True): 
			self.writetolog("unloader->unload")
		if (self.prefs.boolvalue("end") == True):
			os.kill(self.lcd.composerPID(),signal.SIGKILL)
		if (DEBUG == True): 
			self.writetolog("Done")
			
	def writetolog(self, message):
		debuglog = open(module_dir + "log.txt","a")
		debuglog.write(message + "\n")
		debuglog.close

if (DEBUG == True): 
	writetolog("Starting Script...")
	
prefs = preferences()
lcd = lcdconnection(prefs)
check = checker(prefs,lcd)
unload = unloader(prefs,lcd)

if (DEBUG == True): 
	writetolog("All Initialised,... Starting hooks.")

print "Lattyware's xChat G15 Highlighter Plugin Is Now All Loaded."
xchat.hook_server("PRIVMSG", check.check) 
xchat.hook_command("CLEARLCD", lcd.clearscreen, help="/clearlcd clears the LCD and replaces it with startup image.") 
xchat.hook_command("OFFLIGHTS", lcd.offlights, help="/clearlights turns off the lights on the keyboard.")
xchat.hook_command("RELOADG15PREFS", prefs.loadprefs, help="/reloadg15prefs reloads the preferences from config.txt, for the G15 xChat plugin.")
xchat.hook_unload(unload.unload) 
