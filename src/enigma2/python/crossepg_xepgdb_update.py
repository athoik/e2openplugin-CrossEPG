from __future__ import print_function
from __future__ import absolute_import
import six

import xml.etree.cElementTree
import re
import os

if six.PY2:
	import httplib
else:
	import http.client as httplib

from enigma import getDesktop, eTimer
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ProgressBar import ProgressBar
from Components.Sources.Progress import Progress
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_CURRENT_SKIN


from . crossepglib import *
from . crossepg_locale import _

SIFTEAM_HOST = "crossepg.sifteam.eu"


class CrossEPG_Xepgdb_Source(object):
	def __init__(self):
		self.headers_url = ""
		self.descriptors_url = ""
		self.description = ""


class CrossEPG_Xepgdb_Update(Screen):
	def __init__(self, session):
		if (getDesktop(0).size().width() < 800):
			skin = "%s/skins/downloader_sd.xml" % os.path.dirname(sys.modules[__name__].__file__)
			self.isHD = 0
		else:
			skin = "%s/skins/downloader_hd.xml" % os.path.dirname(sys.modules[__name__].__file__)
			self.isHD = 1
		f = open(skin, "r")
		self.skin = f.read()
		f.close()
		Screen.__init__(self, session)
		Screen.__init__(self, session)
		self.skinName = "downloader"
		Screen.setTitle(self, _("CrossEPG"))

		self.sources = []
		self.session = session

		self["background"] = Pixmap()
		self["action"] = Label(_("Updating xepgdb providers..."))
		self["summary_action"] = StaticText(_("Updating rytec providers..."))
		self["status"] = Label("")
		self["progress"] = ProgressBar()
		self["progress"].hide()
		self["progress_text"] = Progress()

		self.config = CrossEPG_Config()
		self.config.load()

		self.timer = eTimer()
		self.timer.callback.append(self.start)

		self.onFirstExecBegin.append(self.firstExec)

	def firstExec(self):
		if self.isHD:
			png = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/crossepg/background_hd.png")
			if png == None or not os.path.exists(png):
				png = "%s/images/background_hd.png" % os.path.dirname(sys.modules[__name__].__file__)
		else:
			png = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/crossepg/background.png")
			if png == None or not os.path.exists(png):
				png = "%s/images/background.png" % os.path.dirname(sys.modules[__name__].__file__)
		self["background"].instance.setPixmapFromFile(png)
		self.timer.start(100, 1)

	def start(self):
		if self.load():
			self.save(self.config.home_directory + "/providers/")
			self.session.open(MessageBox, _("%d providers updated") % len(self.sources), type=MessageBox.TYPE_INFO, timeout=5)
		else:
			self.session.open(MessageBox, _("Cannot retrieve xepgdb sources"), type=MessageBox.TYPE_ERROR, timeout=10)
		self.close()

	def load(self):
		try:
			conn = httplib.HTTPConnection(SIFTEAM_HOST)
			conn.request("GET", "/sources.xml")
			httpres = conn.getresponse()
			print("[crossepg_xepgdb_update] load response = %s" % httpres)			
			if httpres.status == 200:
				f = open("/tmp/crossepg_xepgdb_tmp", "w")
				f.write(httpres.read())
				f.close()
				self.loadFromFile("/tmp/crossepg_xepgdb_tmp")
				os.unlink("/tmp/crossepg_xepgdb_tmp")
				return True
		except Exception as e:
			print("[crossepg_xepgdb_update] exception on load = %s" % e)
		return False

	def loadFromFile(self, filename):
		mdom = xml.etree.cElementTree.parse(filename)
		root = mdom.getroot()

		for node in root:
			if node.tag == "source":
				source = CrossEPG_Xepgdb_Source()
				for childnode in node:
					if childnode.tag == "description":
						source.description = childnode.text
					elif childnode.tag == "headers":
						source.headers = childnode.text
					elif childnode.tag == "descriptors":
						source.descriptors = childnode.text

				self.sources.append(source)

	def save(self, destination):
		os.system("rm -f " + destination + "/xepgdb_*.conf")
		for source in self.sources:
			p = re.compile('[/:()<>|?*\s-]|(\\\)')
			filename = p.sub('_', source.description).lower()
			if filename[:7] != "xepgdb_":
				filename = "xepgdb_" + filename
			f = open(destination + "/" + filename + ".conf", "w")
			f.write("description=" + source.description + "\n")
			f.write("protocol=xepgdb\n")
			f.write("headers_url =" + source.headers + "\n")
			f.write("descriptors_url =" + source.descriptors + "\n")
			f.close()
