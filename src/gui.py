#!/usr/bin/env python3.7
################################################################################
# File:    main.py
# Purpose: This is the code to launch the BusKill GUI app
#          For more info, see: https://buskill.in/
# Authors: Michael Altfield <michael@buskill.in>
# Created: 2020-06-23
# Updated: 2020-06-23
# Version: 0.1
################################################################################

import kivy
#kivy.require('1.0.6') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.label import Label

class BusKill(App):

	def build(self):

		return Label(
		 text = "Welcome to the BusKill App!"
		)

BusKill().run()
