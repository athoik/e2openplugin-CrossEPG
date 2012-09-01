from enigma import *
from crossepglib import *
from crossepg_auto import crossepg_auto
from crossepg_info import CrossEPG_Info
from crossepg_about import CrossEPG_About
from crossepg_providers import CrossEPG_Providers
from crossepg_setup import CrossEPG_Setup
from crossepg_downloader import CrossEPG_Downloader
from crossepg_importer import CrossEPG_Importer
from crossepg_converter import CrossEPG_Converter
from crossepg_loader import CrossEPG_Loader
from crossepg_ordering import CrossEPG_Ordering
from crossepg_rytec_update import CrossEPG_Rytec_Update
from crossepg_xepgdb_update import CrossEPG_Xepgdb_Update
from crossepg_locale import _

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Components.Label import Label
from Components.Sources.StaticText import StaticText
from Components.Button import Button
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.MultiContent import MultiContentEntryText
from Components.Harddisk import harddiskmanager
from Components.PluginComponent import plugins
from Components.ActionMap import ActionMap
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Plugins.Plugin import PluginDescriptor

from time import *


import _enigma

class CrossEPG_Menu(Screen):
	def __init__(self, session):
		if (getDesktop(0).size().width() < 800):
			skin = "%s/skins/menu_sd.xml" % os.path.dirname(sys.modules[__name__].__file__)
		else:
			skin = "%s/skins/menu_hd.xml" % os.path.dirname(sys.modules[__name__].__file__)
		f = open(skin, "r")
		self.skin = f.read()
		f.close()
		Screen.__init__(self, session)
		try:
			from version import version
			self.setup_title = _("CrossEPG") + " - " + version[:5]
			Screen.setTitle(self, self.setup_title)
		except Exception, e:
			self.setup_title = _("CrossEPG") + " - " + _("unknow version")
			Screen.setTitle(self, self.setup_title)

		self.config = CrossEPG_Config()
		self.config.load()
		self.patchtype = getEPGPatchType()

		self.onChangedEntry = [ ]
		l = []
		l.append(self.buildListEntry(_("Configure"), "configure.png"))
		l.append(self.buildListEntry(_("XMLTV providers"), "xmltv.png"))
		l.append(self.buildListEntry(_("OpenTV providers"), "opentv.png"))
		l.append(self.buildListEntry(_("XEPGDB providers"), "xepgdb.png"))
		l.append(self.buildListEntry(_("Scripts providers"), "scripts.png"))
		l.append(self.buildListEntry(_("MHW2 providers"), "opentv.png"))
		l.append(self.buildListEntry(_("Providers start order"), "reorder.png"))
		l.append(self.buildListEntry(_("Update rytec providers"), "rytec_small.png"))
		l.append(self.buildListEntry(_("Update xepgdb providers"), "xepgdb.png"))
		l.append(self.buildListEntry(_("Download now"), "download.png"))
		l.append(self.buildListEntry(_("Force csv import now"), "csv.png"))
		l.append(self.buildListEntry(_("Force epg.dat conversion now"), "conversion.png"))
		l.append(self.buildListEntry(_("Force epg reload"), "reload.png"))
		l.append(self.buildListEntry(_("Info about database"), "dbinfo.png"))
		l.append(self.buildListEntry(_("About"), "about.png"))

		self["list"] = List(l)
		self["setupActions"] = ActionMap(["SetupActions", "MenuActions"],
		{
			"cancel": self.quit,
			"ok": self.openSelected,
			"menu": self.quit,
		}, -2)

		if self.config.configured == 0:
			self.onFirstExecBegin.append(self.openSetup)

	# for summary:
	def changedEntry(self):
		for x in self.onChangedEntry:
			x()

	def getCurrentEntry(self):
		return str(self["list"].getCurrent()[1])

	def getCurrentValue(self):
		return ""

	def createSummary(self):
		return CrossEPG_MenuSummary

	def buildListEntry(self, description, image):
		pixmap = LoadPixmap(cached=True, path="%s/images/%s" % (os.path.dirname(sys.modules[__name__].__file__), image));
		return((pixmap, description))

	def openSetup(self):
		self.session.open(CrossEPG_Setup)

	def openSelected(self):
		index = self["list"].getIndex()
		if index == 0:
			self.session.open(CrossEPG_Setup)
		elif index == 1:
			self.session.open(CrossEPG_Providers, "xmltv")
		elif index == 2:
			self.session.open(CrossEPG_Providers, "opentv")
		elif index == 3:
			self.session.open(CrossEPG_Providers, "xepgdb")
		elif index == 4:
			self.session.open(CrossEPG_Providers, "script")
		elif index == 5:
			self.session.open(CrossEPG_Providers, "mhw2")
		elif index == 6:
			self.session.open(CrossEPG_Ordering)
		elif index == 7:
			self.session.open(CrossEPG_Rytec_Update)
		elif index == 8:
			self.session.open(CrossEPG_Xepgdb_Update)
		elif index == 9:
			self.config.load()
			self.config.deleteLog()
			self.downloader()
		elif index == 10:
			self.importer()
		elif index == 11:
			self.converter()
		elif index == 12:
			self.loader()
		elif index == 13:
			self.session.open(CrossEPG_Info)
		elif index == 14:
			self.session.open(CrossEPG_About)

	def quit(self):
		self.close()

	def downloader(self):
		self.config.load()
		self.session.openWithCallback(self.downloadCallback, CrossEPG_Downloader, self.config.providers)

	def downloadCallback(self, ret):
		if ret:
			if self.config.csv_import_enabled == 1:
				self.importer()
			else:
				if self.patchtype != 3:
					self.converter()
				else:
					self.loader()

	def importer(self):
		self.session.openWithCallback(self.importerCallback, CrossEPG_Importer)

	def importerCallback(self, ret):
		if ret:
			if self.patchtype != 3:
				self.converter()
			else:
				self.loader()

	def converter(self):
		self.session.openWithCallback(self.converterCallback, CrossEPG_Converter)

	def converterCallback(self, ret):
		if ret:
			if self.patchtype != -1:
				self.loader()
			else:
				if self.config.download_manual_reboot:
					from Screens.Standby import TryQuitMainloop
					self.session.open(TryQuitMainloop, 3)

	def loader(self):
		self.session.open(CrossEPG_Loader)

class CrossEPG_MenuSummary(Screen):
	def __init__(self, session, parent):
		Screen.__init__(self, session, parent = parent)
		self["SetupTitle"] = StaticText(_(parent.setup_title))
		self["SetupEntry"] = StaticText("")
		self["SetupValue"] = StaticText("")
		self.onShow.append(self.addWatcher)
		self.onHide.append(self.removeWatcher)

	def addWatcher(self):
		self.parent.onChangedEntry.append(self.selectionChanged)
		self.parent["list"].onSelectionChanged.append(self.selectionChanged)
		self.selectionChanged()

	def removeWatcher(self):
		self.parent.onChangedEntry.remove(self.selectionChanged)
		self.parent["list"].onSelectionChanged.remove(self.selectionChanged)

	def selectionChanged(self):
		self["SetupEntry"].text = self.parent.getCurrentEntry()
		self["SetupValue"].text = self.parent.getCurrentValue()

