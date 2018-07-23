#gui/addonGui.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2012-2018 NV Access Limited, Beqa Gozalishvili, Joseph Lee, Babbage B.V., Ethan Holliger

import os
import wx
import core
import config
import languageHandler
import gui
from logHandler import log
import addonHandler
import globalVars
import buildVersion
import guiHelper
import nvdaControls

class AddonsDialog(wx.Dialog):
	_instance = None
	def __new__(cls, *args, **kwargs):
		if AddonsDialog._instance is None:
			return super(AddonsDialog, cls).__new__(cls, *args, **kwargs)
		return AddonsDialog._instance

	def __init__(self,parent):
		if AddonsDialog._instance is not None:
			return
		AddonsDialog._instance = self
		# Translators: The title of the Addons Dialog
		super(AddonsDialog,self).__init__(parent,title=_("Add-ons Manager"))
		mainSizer=wx.BoxSizer(wx.VERTICAL)
		settingsSizer=wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		if globalVars.appArgs.disableAddons:
			# Translators: A message in the add-ons manager shown when all add-ons are disabled.
			addonsDisabledLabel=wx.StaticText(self,-1,label=_("All add-ons are currently disabled. To enable add-ons you must restart NVDA."))
			mainSizer.Add(addonsDisabledLabel)
		# Translators: the label for the installed addons list in the addons manager.
		entriesLabel=_("Installed Add-ons")
		self.addonsList=sHelper.addLabeledControl(entriesLabel, nvdaControls.AutoWidthColumnListCtrl, style=wx.LC_REPORT|wx.LC_SINGLE_SEL,size=(550,350))
		# Translators: The label for a column in add-ons list used to identify add-on package name (example: package is OCR).
		self.addonsList.InsertColumn(0,_("Package"),width=150)
		# Translators: The label for a column in add-ons list used to identify add-on's running status (example: status is running).
		self.addonsList.InsertColumn(1,_("Status"),width=50)
		# Translators: The label for a column in add-ons list used to identify add-on's version (example: version is 0.3).
		self.addonsList.InsertColumn(2,_("Version"),width=50)
		# Translators: The label for a column in add-ons list used to identify add-on's author (example: author is NV Access).
		self.addonsList.InsertColumn(3,_("Author"),width=300)
		self.addonsList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemSelected)

		entryButtonsHelper=guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: The label for a button in Add-ons Manager dialog to show information about the selected add-on.
		self.aboutButton=entryButtonsHelper.addButton(self,label=_("&About add-on..."))
		self.aboutButton.Disable()
		self.aboutButton.Bind(wx.EVT_BUTTON,self.onAbout)
		# Translators: The label for a button in Add-ons Manager dialog to show the help for the selected add-on.
		self.helpButton=entryButtonsHelper.addButton(self,label=_("Add-on &help"))
		self.helpButton.Disable()
		self.helpButton.Bind(wx.EVT_BUTTON,self.onHelp)
		# Translators: The label for a button in Add-ons Manager dialog to enable or disable the selected add-on.
		self.enableDisableButton=entryButtonsHelper.addButton(self,label=_("&Disable add-on"))
		self.enableDisableButton.Disable()
		self.enableDisableButton.Bind(wx.EVT_BUTTON,self.onEnableDisable)
		# Translators: The label for a button in Add-ons Manager dialog to install an add-on.
		self.addButton=entryButtonsHelper.addButton(self,label=_("&Install..."))
		self.addButton.Bind(wx.EVT_BUTTON,self.onAddClick)
		# Translators: The label for a button to remove either:
		# Remove the selected add-on in Add-ons Manager dialog.
		# Remove a speech dictionary entry.
		self.removeButton=entryButtonsHelper.addButton(self,label=_("&Remove"))
		self.removeButton.Disable()
		self.removeButton.Bind(wx.EVT_BUTTON,self.onRemoveClick)
		# Translators: The label of a button in Add-ons Manager to open the Add-ons website and get more add-ons.
		self.getAddonsButton=entryButtonsHelper.addButton(self,label=_("&Get add-ons..."))
		self.getAddonsButton.Bind(wx.EVT_BUTTON,self.onGetAddonsClick)
		settingsSizer.Add(entryButtonsHelper.sizer)
		mainSizer.Add(settingsSizer,border=20,flag=wx.LEFT|wx.RIGHT|wx.TOP)
		# Translators: The label of a button to close the Addons dialog.
		closeButton = wx.Button(self, label=_("&Close"), id=wx.ID_CLOSE)
		closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		mainSizer.Add(closeButton,border=20,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.CENTER|wx.ALIGN_RIGHT)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.EscapeId = wx.ID_CLOSE
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.refreshAddonsList()
		self.addonsList.SetFocus()
		self.CentreOnScreen()

	def onAddClick(self,evt):
		# Translators: The message displayed in the dialog that allows you to choose an add-on package for installation.
		fd=wx.FileDialog(self,message=_("Choose Add-on Package File"),
		# Translators: the label for the NVDA add-on package file type in the Choose add-on dialog.
		wildcard=(_("NVDA Add-on Package (*.{ext})")+"|*.{ext}").format(ext=addonHandler.BUNDLE_EXTENSION),
		defaultDir="c:",style=wx.FD_OPEN)
		if fd.ShowModal()!=wx.ID_OK:
			return
		addonPath=fd.GetPath()
		self.installAddon(addonPath)

	def installAddon(self, addonPath, closeAfter=False):
		try:
			try:
				bundle=addonHandler.AddonBundle(addonPath)
			except:
				log.error("Error opening addon bundle from %s"%addonPath,exc_info=True)
				# Translators: The message displayed when an error occurs when opening an add-on package for adding. 
				gui.messageBox(_("Failed to open add-on package file at %s - missing file or invalid file format")%addonPath,
					# Translators: The title of a dialog presented when an error occurs.
					_("Error"),
					wx.OK | wx.ICON_ERROR)
				return
			# Translators: The message displayed to give information about the compatibility of this add-on with certain NVDA versions.
			versionInfoMessage = _(
				"The minimum compatible NVDA version for this add-on is {minimumNVDAVersion}.\n"
				"The last version of NVDA this add-on has been reported to work with is {lastTestedNVDAVersion}"
			).format(
				# Translators: Displayed in the compatibility message when a version is unknown.
				minimumNVDAVersion=bundle.manifest['minimumNVDAVersion'] or _("unknown"),
				lastTestedNVDAVersion=bundle.manifest['lastTestedNVDAVersion'] or _("unknown")
			)
			if bundle.isBlacklisted:
				# Translators: The message displayed when installing an add-on package is prohibited.
				incompatibleMessage = _(
					"The installation of {summary} {version} by {author} has been blocked for "
					"installation within NVDA version {NVDAVersion}.\n{versionInfoMessage}"
				).format(
					NVDAVersion="%d.%d (%s)"%(
						buildVersion.version_year, buildVersion.version_major, buildVersion.version
					) if buildVersion.isTestVersion else buildVersion.version,
					versionInfoMessage=versionInfoMessage, **bundle.manifest
				)
				gui.messageBox(incompatibleMessage,
					# Translators: The title of a dialog presented when an error occurs.
					_("Error"),
					wx.OK | wx.ICON_ERROR)
				return

			# Translators: A message asking the user if they really wish to install an addon.
			if gui.messageBox(_(
				"Are you sure you want to install this add-on? "
				"Only install add-ons from trusted sources.\n"
				"Addon: {summary} {version}\nAuthor: {author}\n{versionInfoMessage}"
			).format(versionInfoMessage=versionInfoMessage,**bundle.manifest),
				# Translators: Title for message asking if the user really wishes to install an Addon.
				_("Add-on Installation"),
				wx.YES|wx.NO|wx.ICON_WARNING)!=wx.YES:
				return
			prevAddon=None
			for addon in self.curAddons:
				if not addon.isPendingRemove and bundle.name==addon.manifest['name']:
					prevAddon=addon
					break
			if prevAddon:
				summary=bundle.manifest["summary"]
				curVersion=prevAddon.manifest["version"]
				newVersion=bundle.manifest["version"]
				if gui.messageBox(
					# Translators: A message asking if the user wishes to update an add-on with the same version currently installed according to the version number.
					_("You are about to install version {newVersion} of {summary}, which appears to be already installed. Would you still like to update?").format(
						summary=summary,
						newVersion=newVersion
					)
					if curVersion==newVersion else 
					# Translators: A message asking if the user wishes to update a previously installed add-on with this one.
					_("A version of this add-on is already installed. Would you like to update {summary} version {curVersion} to version {newVersion}?").format(
						summary=summary,
						curVersion=curVersion,
						newVersion=newVersion
					),
					# Translators: A title for the dialog  asking if the user wishes to update a previously installed add-on with this one.
					_("Add-on Installation"),
					wx.YES|wx.NO|wx.ICON_WARNING)!=wx.YES:
						return
				prevAddon.requestRemove()
			progressDialog = gui.IndeterminateProgressDialog(gui.mainFrame,
			# Translators: The title of the dialog presented while an Addon is being installed.
			_("Installing Add-on"),
			# Translators: The message displayed while an addon is being installed.
			_("Please wait while the add-on is being installed."))
			try:
				gui.ExecAndPump(addonHandler.installAddonBundle,bundle)
			except:
				log.error("Error installing  addon bundle from %s"%addonPath,exc_info=True)
				self.refreshAddonsList()
				progressDialog.done()
				del progressDialog
				# Translators: The message displayed when an error occurs when installing an add-on package.
				gui.messageBox(_("Failed to install add-on  from %s")%addonPath,
					# Translators: The title of a dialog presented when an error occurs.
					_("Error"),
					wx.OK | wx.ICON_ERROR)
				return
			else:
				self.refreshAddonsList(activeIndex=-1)
				progressDialog.done()
				del progressDialog
		finally:
			if closeAfter:
				# #4460: If we do this immediately, wx seems to drop the WM_QUIT sent if the user chooses to restart.
				# This seems to have something to do with the wx.ProgressDialog.
				# The CallLater seems to work around this.
				wx.CallLater(1, self.Close)

	def onRemoveClick(self,evt):
		index=self.addonsList.GetFirstSelected()
		if index<0: return
		# Translators: Presented when attempting to remove the selected add-on.
		if gui.messageBox(_("Are you sure you wish to remove the selected add-on from NVDA?"),
			# Translators: Title for message asking if the user really wishes to remove the selected Addon.
			_("Remove Add-on"), wx.YES_NO|wx.ICON_WARNING) != wx.YES: return
		addon=self.curAddons[index]
		addon.requestRemove()
		self.refreshAddonsList(activeIndex=index)
		self.addonsList.SetFocus()

	def getAddonStatus(self,addon):
		statusList = []
		if addon.isRunning:
			# Translators: The status shown for an addon when its currently running in NVDA.
			statusList.append(_("enabled"))
		elif globalVars.appArgs.disableAddons or addon.isDisabled:
			# Translators: The status shown for an addon when its currently suspended do to addons being disabled.
			statusList.append(_("disabled"))
		elif addon.isPendingInstall:
			# Translators: The status shown for a newly installed addon before NVDA is restarted.
			statusList.append(_("install"))
		if addon.isPendingRemove:
			# Translators: The status shown for an addon that has been marked as removed, before NVDA has been restarted.
			statusList.append(_("removed after restart"))
		elif addon.isPendingDisable:
			# Translators: The status shown for an addon when it requires a restart to become disabled
			statusList.append(_("Disabled after restart"))
		elif addon.isPendingEnable:
			# Translators: The status shown for an addon when it requires a restart to become enabled
			statusList.append(_("Enabled after restart"))
		if addon.isBlacklisted:
			# Translators: The status shown for an addon when it's added to the blacklist.
			statusList.append(_("blacklisted"))
		elif addon.isWhitelisted:
			# Translators: The status shown for an addon when it's added to the whitelist.
			statusList.append(_("whitelisted"))
		return ", ".join(statusList)

	def refreshAddonsList(self,activeIndex=0):
		self.addonsList.DeleteAllItems()
		self.curAddons=[]
		for addon in addonHandler.getAvailableAddons():
			self.addonsList.Append((addon.manifest['summary'], self.getAddonStatus(addon), addon.manifest['version'], addon.manifest['author']))
			self.curAddons.append(addon)
		# select the given active addon or the first addon if not given
		curAddonsLen=len(self.curAddons)
		if curAddonsLen>0:
			if activeIndex==-1:
				activeIndex=curAddonsLen-1
			elif activeIndex<0 or activeIndex>=curAddonsLen:
				activeIndex=0
			self.addonsList.Select(activeIndex,on=1)
			self.addonsList.SetItemState(activeIndex,wx.LIST_STATE_FOCUSED,wx.LIST_STATE_FOCUSED)
		else:
			self.aboutButton.Disable()
			self.helpButton.Disable()
			self.removeButton.Disable()

	def _shouldDisable(self, addon):
		return not (addon.isPendingDisable or (addon.isDisabled and not addon.isPendingEnable))

	def onListItemSelected(self, evt):
		index=evt.GetIndex()
		addon=self.curAddons[index] if index>=0 else None
		# #3090: Change toggle button label to indicate action to be taken if clicked.
		if addon is not None:
			# Translators: The label for a button in Add-ons Manager dialog to enable or disable the selected add-on.
			self.enableDisableButton.SetLabel(_("&Enable add-on") if not self._shouldDisable(addon) else _("&Disable add-on"))
		self.aboutButton.Enable(addon is not None and not addon.isPendingRemove)
		self.helpButton.Enable(bool(addon is not None and not addon.isPendingRemove and addon.getDocFilePath()))
		self.enableDisableButton.Enable(addon is not None and not addon.isPendingRemove and not addon.isBlacklisted)
		self.removeButton.Enable(addon is not None and not addon.isPendingRemove)

	def onClose(self,evt):
		self.DestroyChildren()
		self.Destroy()
		# #7077: If the instance flag isn't cleared, it causes issues when add-ons manager reopens or another add-on is installed remotely.
		AddonsDialog._instance = None
		needsRestart = False
		for addon in self.curAddons:
			if (addon.isPendingInstall or addon.isPendingRemove
				or addon.isDisabled and addon.isPendingEnable
				or addon.isRunning and addon.isPendingDisable):
				needsRestart = True
				break
		if needsRestart:
			# Translators: A message asking the user if they wish to restart NVDA as addons have been added, enabled/disabled or removed. 
			if gui.messageBox(_("Changes were made to add-ons. You must restart NVDA for these changes to take effect. Would you like to restart now?"),
			# Translators: Title for message asking if the user wishes to restart NVDA as addons have been added or removed. 
			_("Restart NVDA"),
			wx.YES|wx.NO|wx.ICON_WARNING)==wx.YES:
				core.restart()

	def onAbout(self,evt):
		index=self.addonsList.GetFirstSelected()
		if index<0: return
		manifest=self.curAddons[index].manifest
		# Translators: message shown in the Addon Information dialog. 
		message=_("""{summary} ({name})
Version: {version}
Author: {author}
Description: {description}
""").format(**manifest)
		url=manifest.get('url')
		if url: 
			# Translators: the url part of the About Add-on information
			message+=_("URL: {url}").format(url=url)
		minimumNVDAVersion=manifest['minimumNVDAVersion']
		if minimumNVDAVersion:
			# Translators: the minimum NVDA version part of the About Add-on information
			message+=_("Minimum required NVDA version: {version}").format(version=minimumNVDAVersion)
		lastTestedNVDAVersion=manifest['lastTestedNVDAVersion']
		if lastTestedNVDAVersion:
			# Translators: the last NVDA version tested part of the About Add-on information
			message+=_("Last NVDA version tested: {version}").format(version=lastTestedNVDAVersion)
		# Translators: title for the Addon Information dialog
		title=_("Add-on Information")
		gui.messageBox(message, title, wx.OK)

	def onHelp(self, evt):
		index = self.addonsList.GetFirstSelected()
		if index < 0:
			return
		path = self.curAddons[index].getDocFilePath()
		os.startfile(path)

	def onEnableDisable(self, evt):
		index=self.addonsList.GetFirstSelected()
		if index<0: return
		addon=self.curAddons[index]
		shouldDisable = self._shouldDisable(addon)
		# Counterintuitive, but makes sense when context is taken into account.
		try:
			addon.enable(not shouldDisable)
		except addonHandler.AddonError:
			log.error("Couldn't change state for %s add-on"%addon.name, exc_info=True)
			gui.messageBox(
				# Translators: The message displayed when the state of an add-on cannot be changed.
				_("Could not {state} the {description} add-on.").format(
					state=_("disable") if shouldDisable else _("enable"),
					description=addon.manifest['summary']
				), 
				# Translators: The title of a dialog presented when an error occurs.
				_("Error"),
				wx.OK | wx.ICON_ERROR)
			return

		self.enableDisableButton.SetLabel(_("&Enable add-on") if shouldDisable else _("&Disable add-on"))
		self.refreshAddonsList(activeIndex=index)

	def onGetAddonsClick(self,evt):
		ADDONS_URL = "http://addons.nvda-project.org"
		os.startfile(ADDONS_URL)

	def __del__(self):
		AddonsDialog._instance = None

	@classmethod
	def handleRemoteAddonInstall(cls, addonPath):
		# Add-ons cannot be installed into a Windows store version of NVDA
		if config.isAppX:
			# Translators: The message displayed when an add-on cannot be installed due to NVDA running as a Windows Store app 
			gui.messageBox(_("Add-ons cannot be installed in the Windows Store version of NVDA"), 
				# Translators: The title of a dialog presented when an error occurs.
				_("Error"),
				wx.OK | wx.ICON_ERROR)
			return
		closeAfter = AddonsDialog._instance is None
		dialog = AddonsDialog(gui.mainFrame)
		dialog.installAddon(addonPath, closeAfter=closeAfter)
		del dialog

class AddonSelectionDialog(wx.Dialog):
	"""A dialog that presents filtered add-ons in a checkable list,
	allowing actions to be performed with the result."""
	_instance = None
	def __new__(cls, *args, **kwargs):
		if AddonSelectionDialog._instance is None:
			return super(AddonSelectionDialog, cls).__new__(cls, *args, **kwargs)
		return AddonSelectionDialog._instance

	def __init__(self,parent, title, message, addonFilterFunc):
		if AddonSelectionDialog._instance is not None:
			return
		AddonSelectionDialog._instance = self
		super(AddonSelectionDialog,self).__init__(parent,title=title)
		self.addonFilterFunc = filterFunc
		mainSizer=wx.BoxSizer(wx.VERTICAL)
		settingsSizer=wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		AddonSelectionIntroLabel=wx.StaticText(self, label=message)
		mainSizer.Add(AddonSelectionIntroLabel)
		# Translators: the label for the addons list in the addon selection dialog.
		entriesLabel=_("Add-ons")
		self.addonsList=sHelper.addLabeledControl(entriesLabel, wx.CheckListBox, size=(550,350))
		self.addonsList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemSelected)

		mainSizer.Add(settingsSizer,border=20,flag=wx.LEFT|wx.RIGHT|wx.TOP)
		# Translators: The label of a button to close the Addons dialog.
		closeButton = wx.Button(self, label=_("&Close"), id=wx.ID_CLOSE)
		closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.Close())
		mainSizer.Add(closeButton,border=20,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.CENTER|wx.ALIGN_RIGHT)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.EscapeId = wx.ID_CLOSE
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.refreshAddonsList()
		self.addonsList.SetFocus()
		self.CentreOnScreen()

	def refreshAddonsList(self,activeIndex=0):
		self.addonsList.DeleteAllItems()
		self.curAddons=[]
		for addon in addonHandler.getAvailableAddons(filterFunc=self.addonFilterFunc):
			self.addonsList.Append((addon.manifest['summary'], self.getAddonStatus(addon), addon.manifest['version'], addon.manifest['author']))
			self.curAddons.append(addon)
		# select the given active addon or the first addon if not given
		curAddonsLen=len(self.curAddons)
		if curAddonsLen>0:
			if activeIndex==-1:
				activeIndex=curAddonsLen-1
			elif activeIndex<0 or activeIndex>=curAddonsLen:
				activeIndex=0
			self.addonsList.Select(activeIndex,on=1)
			self.addonsList.SetItemState(activeIndex,wx.LIST_STATE_FOCUSED,wx.LIST_STATE_FOCUSED)
		else:
			self.aboutButton.Disable()
			self.helpButton.Disable()

	def onListItemSelected(self, evt):
		index=evt.GetIndex()
		addon=self.curAddons[index] if index>=0 else None
		self.aboutButton.Enable(addon is not None and not addon.isPendingRemove)
		self.helpButton.Enable(bool(addon is not None and not addon.isPendingRemove and addon.getDocFilePath()))

	def onClose(self,evt):
		self.DestroyChildren()
		self.Destroy()
		AddonSelectionDialog._instance = None

	def __del__(self):
		AddonSelectionDialog._instance = None
