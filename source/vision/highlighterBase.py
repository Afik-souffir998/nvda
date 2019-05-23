#vision/highlighterBase.py
#A part of NonVisual Desktop Access (NVDA)
#This file is covered by the GNU General Public License.
#See the file COPYING for more details.
#Copyright (C) 2018-2019 NV Access Limited, Babbage B.V.

"""Module containing the highglighter base class.
A highlighter is used to highlight important areas of the screen (e.g. the focus, mouse or review position).
"""

from .providerBase import VisionEnhancementProvider, ProviderEventAdapter
from abc import abstractmethod
import driverHandler
from .constants import ROLE_HIGHLIGHTER

class Highlighter(VisionEnhancementProvider):
	"""A vision enhancement provider that supports highlighting certain portions of the screen.
	Subclasses should at least implement the L{initializeHighlighter},
	L{terminateHighlighter} and L{refresh} methods.
	Supported contexts should be listed in L{supportedHighlightContexts}.
	"""

# as far as I can tell this isn't used to provide differences in behaviour?

	__role = ROLE_HIGHLIGHTER
	_event_adapter_class = HighlighterEventAdaptor

	#: Tuple of supported contexts for this highlighter.
	supportedHighlightContexts = tuple()

	@abstractmethod
	def initializeHighlighter(self):
		"""Initializes a highlighter.
		Subclasses must extend this method.
		"""
		#: A dictionary that maps contexts to their current rectangle.
		self.contextToRectMap = {}
		# Initialize the map with their current values
		for context in self.enabledHighlightContexts:
			# Always call the base implementation here
			Highlighter.updateContextRect(self, context)

	@abstractmethod
	def terminateHighlighter(self):
		"""Terminates a highlighter.
		Subclasses must extend this method.
		"""
		self.contextToRectMap.clear()

	@classmethod
	def HighlightSetting(cls, context, displayName, defaultVal=True):
		"""Factory function for creating highlight setting."""
		return driverHandler.BooleanDriverSetting(
			'highlight%s' % (context[0].upper() + context[1:]),
			displayName,
			defaultVal=defaultVal
		)

	def updateContextRect(self, context, rect=None, obj=None):
		"""Updates the position rectangle of the highlight for the specified context.
		The base implementation updates the position in the L{contextToRectMap}.
		If rect and obj are C{None}, the position is retrieved from the object associated with the context.
		Otherwise, either L{obj} or L{rect} should be provided.
		Subclasses should extend or override this method if they want to get the context position in a different way.
		"""
		if context not in self.enabledHighlightContexts:
			return
		if rect is not None and obj is not None:
			raise ValueError("Only one of rect or obj should be provided")
		if rect is None:
			try:
				rect= self.getContextRect(context, obj)
			except (LookupError, NotImplementedError):
				rect = None
		self.contextToRectMap[context] = rect

	@abstractmethod
	def refresh(self):
		"""Refreshes the screen positions of the enabled highlights.
		This is called once in every core cycle.
		Subclasses must override this method.
		"""
		raise NotImplementedError

	def _get_enabledHighlightContexts(self):
		"""Gets the contexts for which the highlighter is enabled.
		If L{enabled} is C{False} this returns an empty tuple.
		"""
		return tuple(
			context for context in self.supportedHighlightContexts
			if getattr(self, 'highlight%s' % (context[0].upper() + context[1:]))
		)

class HighlighterEventAdaptor(ProviderEventAdapter):
	def __init__(self, highlighter):
		"""
		:param magnifier:
		:type magnifier: Magnifier
		"""
		self.highlighter = highlighter

	def handleForeground(self, obj):
			self.highlighter.updateContextRect(CONTEXT_FOREGROUND, obj=obj)

	def handleGainFocus(self, obj):
		self.highlighter.updateContextRect(CONTEXT_FOCUS, obj=obj)
		if config.conf['reviewCursor']['followFocus']:
			# Purposely don't provide the object to updateContextRect here.
			# This is because obj could also be a tree interceptor.
			# Furthermore, even when review follows focus, there might be
			# reasons why the navigator object is not the same as the focus object.
			self.highlighter.updateContextRect(CONTEXT_NAVIGATOR)
		if not mightHaveCaret: # this is an error, not sure how to fix.
			# If this object does not have a caret, clear the caret rectangle from the map
			# However, in the unlikely case it yet has a caret, we want to highlight that.
			self.highlighter.updateContextRect(CONTEXT_CARET, obj=obj)

	def handlePendingCaretUpdate(self, lastCaretObj, context):
		self.highlighter.updateContextRect(context, obj=lastCaretObj)

	def handlePendingReviewUpdate(self, lastReviewMoveContext):
		for context in (
				CONTEXT_NAVIGATOR,
				CONTEXT_REVIEW
		):
			self.highlighter.updateContextRect(context=context)

	def handleMouseMove(self, obj, x, y):
		# highlighter doesn't care about the mouse.
		pass
