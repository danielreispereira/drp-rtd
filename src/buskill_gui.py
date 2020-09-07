#!/usr/bin/env python3.7
"""
::

  File:    buskill_gui.py
  Authors: Michael Altfield <michael@buskill.in>
  Created: 2020-06-23
  Updated: 2020-06-23
  Version: 0.1

This is the code to launch the BusKill GUI app

For more info, see: https://buskill.in/
"""

################################################################################
#                                   IMPORTS                                    #
################################################################################

import packages.buskill
from packages.garden.navigationdrawer import NavigationDrawer
from packages.garden.progressspinner import ProgressSpinner

import os, webbrowser

import multiprocessing
from multiprocessing import util

import logging
util.get_logger().setLevel(util.DEBUG)
multiprocessing.log_to_stderr().setLevel( logging.DEBUG )
#from multiprocessing import get_context

import kivy
#kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock

from kivy.core.window import Window
Window.size = ( 300, 500 )

from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView

# grey background color
Window.clearcolor = [ 0.188, 0.188, 0.188, 1 ]

from kivy.config import Config
Config.set('kivy', 'exit_on_escape', '0')
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

from kivy.core.text import LabelBase

import logging
logger = logging.getLogger( __name__ )

################################################################################
#                                  SETTINGS                                    #
################################################################################

# n/a

################################################################################
#                                   CLASSES                                    #
################################################################################

class MainWindow(BoxLayout):

	toggle_btn = ObjectProperty(None)
	status = ObjectProperty(None)
	menu = ObjectProperty(None)
	actionview = ObjectProperty(None)

	dialog = None

	def __init__(self, **kwargs):
		global bk
		self.bk = bk
		super(BoxLayout, self).__init__(**kwargs)

	def toggle_menu(self):

		self.nav_drawer.toggle_state()

	def toggle_buskill(self):

		self.bk.toggle()

		if self.bk.is_armed:
			self.toggle_btn.text = 'Disarm'
			self.status.text = 'BusKill is currently armed.'
			self.toggle_btn.md_bg_color = [1,0,0,1]
			self.toggle_btn.background_color = self.color_red
			self.actionview.background_color = self.color_red
		else:
			self.toggle_btn.text = 'Arm'
			self.status.text = 'BusKill is currently disarmed.'
			self.toggle_btn.background_color = self.color_primary
			self.actionview.background_color = self.color_primary

	def update1(self):

		# first close the navigation drawer
		self.nav_drawer.toggle_state()

		msg = "Checking for updates requires internet access.\n\n"
		msg+= "Would you like to check for updates now?"

		self.dialog = DialogConfirmation(
		 title='Check for Updates?',
		 body = msg,
		 button='Check Updates',
		 continue_function=self.update2,
		)
		self.dialog.open()

	def update2(self):

		# close the dialog if it's already opened
		if self.dialog != None:
			self.dialog.dismiss()

		# open a new dialog with a spinning progress circle that tells the user
		# to wait for upgrade() to finish
		msg = "Please wait while we check for updates and download the latest version of BusKill."

		self.dialog = DialogConfirmation(
		 title='Updating BusKill',
		 body = msg,
		 button = "",
		 continue_function=None,
		)
		self.dialog.b_cancel.on_release = self.upgrade_cancel
		self.dialog.auto_dismiss = False

		progress_spinner = ProgressSpinner( color = self.color_primary )
		self.dialog.dialog_contents.add_widget( progress_spinner, 2 )
		self.dialog.dialog_contents.add_widget( Label( text='' ), 2 )
		self.dialog.size_hint = (0.9,0.9)

		self.dialog.open()

		# TODO: split this upgrade function into update() and upgrade() and
		# make the status somehow accessible from here so we can put it in a modal

		# Call the upgrade_bg() function which executes the upgrade() function in
		# an asynchronous process so it doesn't block the UI
		self.bk.upgrade_bg()

		# Register the upgrade3_tick() function as a callback to be executed
		# every second, and we'll use that to update the UI with a status
		# message from the upgrade() process and check to see if it the upgrade
		# finished running
		Clock.schedule_interval(self.upgrade3_tick, 1)

	# cancel the upgrade()
	def upgrade_cancel( self ):

		Clock.unschedule( self.upgrade3_tick )
		print( self.bk.upgrade_bg_terminate() )

	# this is the callback function that will be executed every one second
	# while buskill's upgrade() method is running
	def upgrade3_tick( self, dt ):
		print( "called upgrade3_tick()" )

		# update the dailog 
		self.dialog.l_body.text = bk.get_upgrade_status()

		# did the upgrade process finish?
		if self.bk.upgrade_is_finished():
			# the call to upgrade() finished.
			Clock.unschedule( self.upgrade3_tick )

			try:
				self.upgrade_result = self.bk.get_upgrade_result()

			except Exception as e:
				# if the update failed for some reason, alert the user

				# close the dialog if it's already opened
				if self.dialog != None:
					self.dialog.dismiss()

				# open a new dialog that tells the user the error that occurred
				self.dialog = DialogConfirmation(
				 title = '[font=mdicons][size=30]\ue002[/size][/font] Update Failed!',
				 body = "",
				 button = "",
				 continue_function=None
				)
				self.dialog.l_title.text = '[font=mdicons][size=30]\ue002[/size][/font] Update Failed!'
				self.dialog.l_body.text = str(e)
				self.dialog.b_cancel.text = "OK"
				self.dialog.open()

				return

			# cleanup the pool used to launch upgrade() asynchronously asap
#			self.upgrade_pool.close()
#			self.upgrade_pool.join()

			# 1 = poll was successful; we're on the latest version
			if self.upgrade_result == '1':

				# close the dialog if it's already opened
				if self.dialog != None:
					self.dialog.dismiss()

				# open a new dialog that tells the user that they're already
				# running the latest version
				self.dialog = DialogConfirmation(
				 title = '[font=mdicons][size=30]\ue92f[/size][/font] Update BusKill',
				 body = "You're currently using the latest version",
				 button = "",
				 continue_function=None
				)
				self.dialog.b_cancel.text = "OK"
				self.dialog.open()
				return

			# if we made it this far, it means that the we successfully finished
			# downloading and installing the latest possible version, and the
			# result is the path to that new executable

			# close the dialog if it's already opened
			if self.dialog != None:
				self.dialog.dismiss()

			# open a new dialog that tells the user that the upgrade() was a
			# success and gets confirmation from the user to restart the app
			msg = "BusKill was updated successfully. Please restart this app to continue."
			self.dialog = DialogConfirmation(
			 title = '[font=mdicons][size=30]\ue92f[/size][/font]  Update Successful',
			 body = msg,
			 button='Restart Now',
			 continue_function = self.update3_restart,
			)
			self.dialog.open()

	def update3_restart( self ):

		msg = "DEBUG: Exiting and launching " +str(self.upgrade_result)
		print( msg ); logging.debug( msg )

		# replace this process with the newer version
		os.execv( self.upgrade_result, [self.upgrade_result] )

class DialogConfirmation(ModalView):

	title = StringProperty(None)
	body = StringProperty(None)
	button = StringProperty(None)
	continue_function = ObjectProperty(None)

	b_continue = ObjectProperty(None)

	def __init__(self, **kwargs):

		self._parent = None
		super(ModalView, self).__init__(**kwargs)

		if self.button == "":
			self.b_continue.parent.remove_widget( self.b_continue )
		else:
			self.b_continue.text = self.button

class CriticalError(BoxLayout):

	msg = ObjectProperty(None)

	def showError( self, msg ):
		self.msg.text = msg

	def fileBugReport( self ):
		# TODO: make this a redirect on buskill.in so old versions aren't tied
		#       to github.com
		webbrowser.open( 'https://docs.buskill.in/buskill-app/en/stable/support.html' )

class BusKillApp(App):

	# register font aiases so we don't have to specify their full file path
	# when setting font names in our kivy language .kv files
	LabelBase.register( "Roboto", "fonts/Roboto-Regular.ttf",  )
	LabelBase.register( "RobotoMedium", "fonts/Roboto-Medium.ttf",  )
	LabelBase.register( "mdicons", "fonts/MaterialIcons-Regular.ttf" )

	global bk
	bk = packages.buskill.BusKill()

	# does rapid-fire UI-agnostic cleanup stuff when the GUI window is closed
	def close( self, *args ):
		bk.close()

	def build(self):

		global bk
		self.bk = bk

		# is the OS that we're running on supported?
		if self.bk.IS_PLATFORM_SUPPORTED:

			# yes, this platform is supported; show the main window
			Window.bind( on_request_close = self.close )
			return MainWindow()

		else:
			# the current platform isn't supported; show critical error window

			msg = buskill.ERR_PLATFORM_NOT_SUPPORTED
			print( msg ); logging.error( msg )

			crit = CriticalError()
			crit.showError( buskill.ERR_PLATFORM_NOT_SUPPORTED )
			return crit
