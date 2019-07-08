# -*- coding: utf-8 -*-

# 1 of 3 experiments developed to replicate both:
# McLaughlin, Shore, & Klein (2001) ~ Wherein T1 difficulty was mixed within blocks
# Shore, McLaughlin, & Klein (2001) ~ Wherein T1 diffculty was blocked

# The 3 experiements are structured as follows:
# MSK_Combined: 3 blocks of blocked T1 difficulty & 3 blocks of mixed T1 difficulty (present paradigm)
# MSK_Mixed: 15 blocks of mixed T1 difficulty
# MSK_Blocked: 3 blocks of blocked T1 difficulty

__author__ = "Brett Feltmate"

import klibs
from klibs import P
from klibs.KLConstants import STROKE_INNER, TK_S, NA, RC_KEYPRESS
from klibs.KLUtilities import *
from klibs.KLKeyMap import KeyMap
from klibs.KLUserInterface import any_key, ui_request
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLGraphics.KLDraw import *
from klibs.KLResponseCollectors import ResponseCollector
from klibs.KLEventInterface import TrialEventTicket as ET
from klibs.KLCommunication import message
from klibs.KLExceptions import TrialException
from klibs.KLTime import Stopwatch

# Import required external libraries
import sdl2
import time
import random
import math
import aggdraw # For drawing mask cells in a single texture
import numpy as np
from PIL import Image

# Define some useful constants
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
EASY = "easy"
MEDIUM = 'medium'
HARD = "hard"

letters = ['A', 'B', 'C', 'D', 'E', 'F',
		   'G', 'H', 'J', 'K', 'L', 'M', 
		   'N', 'P', 'Q', 'R', 'S', 'T', 
		   'U', 'V', 'W', 'X', 'Y', 'Z']


class MSK_Mixed(klibs.Experiment):

	# Establishes factors held constant throughout experiment
	def setup(self):
		# Stimulus durations
		# T2|M2|ISI durations held constant
		# Note: all durations are in units of refresh_time (16.67ms)
		self.t2_duration = P.refresh_time * 2 # 33ms
		self.m2_duration = P.refresh_time * 4 # 66ms
		self.isi = P.refresh_time # 16ms

		# T1 duration sets
		self.t1_timings = { 
			# 50.01ms | 50.01ms
			EASY:[P.refresh_time * 3, P.refresh_time * 3], 
			# 33.33ms | 66.66ms
			MEDIUM:[P.refresh_time * 2, P.refresh_time * 4], 
			# 16.67ms | 83.33ms
			HARD:[P.refresh_time, P.refresh_time * 5] }

		# Stimulus sizes
		fix_thickness = deg_to_px(0.1)
		fix_size = deg_to_px(0.6)
		target_size = deg_to_px(0.6)

		# Init drawbjects
		self.fixation = FixationCross(size=fix_size, thickness=fix_thickness, fill=BLACK)

		# Experiment messages
		self.anykey_txt = "{0}\nPress any key to continue..."
		self.practice_txt = '{0}\n(PRACTICE ROUND)'
		self.t1_id_request = "What was the first letter? If unsure, make your best guess."
		self.t2_id_request = "What was the second letter? If unsure, make your best guess."

		# Initialize ResponseCollectors
		self.t1_rc = ResponseCollector(uses=RC_KEYPRESS)
		self.t2_rc = ResponseCollector(uses=RC_KEYPRESS)

		# Initialize ResponseCollector Keymaps
		self.keymap = KeyMap(
			'identity_response', letters, letters,
			[sdl2.SDLK_a, sdl2.SDLK_b, sdl2.SDLK_c, sdl2.SDLK_d, sdl2.SDLK_e, sdl2.SDLK_f,
			 sdl2.SDLK_g, sdl2.SDLK_h, sdl2.SDLK_j, sdl2.SDLK_k, sdl2.SDLK_l, sdl2.SDLK_m,
			 sdl2.SDLK_n, sdl2.SDLK_p, sdl2.SDLK_q, sdl2.SDLK_r, sdl2.SDLK_s, sdl2.SDLK_t, 
			 sdl2.SDLK_u, sdl2.SDLK_v, sdl2.SDLK_w, sdl2.SDLK_x, sdl2.SDLK_y, sdl2.SDLK_z]
		)

		# Insert practice block at beginning
		if P.run_practice_blocks:
			self.insert_practice_block(1, trial_counts=30)

	# Establishes block-wise factors
	def block(self):
		# Inform participant as to their progress
		block_txt = "Block {0} of {1}".format(P.block_number, P.blocks_per_experiment)

		if P.practicing: 
			block_txt = self.practice_txt.format(block_txt)

		progress_txt = block_txt.format(self.anykey_txt)

		self.present_txt(progress_txt)

	# Set response collector parameters
	def setup_response_collector(self):
		self.t1_rc.terminate_after = [10, TK_S]					# Timeout after 10s of no response
		self.t1_rc.display_callback = self.identity_callback	# Request identity response
		self.t1_rc.display_kwargs = {'target': 'T1'}			# Specify which response to request
		self.t1_rc.keypress_listener.key_map = self.keymap		# Set which responses are allowed
		self.t1_rc.keypress_listener.interrupts = True			# Abort collection once response made

		self.t2_rc.terminate_after = [10, TK_S]
		self.t2_rc.display_callback = self.identity_callback
		self.t2_rc.display_kwargs = {'target': 'T2'}
		self.t2_rc.keypress_listener.key_map = self.keymap
		self.t2_rc.keypress_listener.interrupts = True

	# Any trials factors that can be established prior to trial onset are set here
	def trial_prep(self):
		# Select target stimuli & durations
		self.t1_identity, self.t2_identity = random.sample(letters,2)
		self.t1_duration, self.m1_duration = self.t1_timings[self.t1_difficulty]
		
		# Init EventManager
		events = [[self.isoa, "T1_on"]]										# Present T1 after some SOA from initiation
		events.append([events[-1][0] + self.t1_duration, 'T1_off'])			# Remove T1 after its duration period
		events.append([events[-1][0] + self.isi, "T1_mask_on"])				# Present M1 shortly after T1 offset
		events.append([events[-1][0] + self.m1_duration, 'T1_mask_off'])	# Remove M1 after its duration period
		events.append([events[-4][0] + self.ttoa, 'T2_on']) 				# TTOA = Time between onset of T1 & T2
		events.append([events[-1][0] + self.t2_duration, 'T2_off'])			# Remove T2 after its duration period
		events.append([events[-1][0] + self.isi, 'T2_mask_on'])				# Present M2 shortly after T2 offset
		events.append([events[-1][0] + self.m2_duration, 'T2_mask_off'])	# Remove M2 after its duration period

		# Register events to EventManager
		for e in events:
			self.evm.register_ticket(ET(e[1],e[0]))

		# Prepare stimulus stream
		self.tmtm_stream = self.prep_stream()

		# Hide mouse cursor during trial
		hide_mouse_cursor()

		# Present fix and wait until initiation response before beginning tiral sequence
		self.present_fixation()

	def trial(self):
		while self.evm.before('T1_on', True): ui_request()			# Variable delay following trial initiation

		self.blit_it(self.tmtm_stream['t1_target'])					# Blit T1 to screen
		while self.evm.before('T1_off', True): ui_request()			# Wait (conditional duration)
		self.flip_it()												# Remove T1

		while self.evm.before('T1_mask_on', True): ui_request() 	# Wait (ISI; fixed at ~17ms)

		self.blit_it(self.tmtm_stream['t1_mask'])					# Blit M1 to screen
		while self.evm.before('T1_mask_off', True): ui_request()	# Wait (conditional duration)
		self.flip_it()												# Remove M1

		while self.evm.before('T2_on', True): ui_request()			# Wait (TTOA)

		self.blit_it(self.tmtm_stream['t2_target'])					# Blit T2 to screen
		while self.evm.before('T2_off', True): ui_request()			# Wait (fixed at ~50ms)
		self.flip_it()												# Remove T2

		while self.evm.before('T2_mask_on', True): ui_request()		# Wait (ISI; fixed at ~17ms)

		self.blit_it(self.tmtm_stream['t2_mask'])					# Blit M2 to screen
		while self.evm.before('T2_mask_off', True): ui_request()	# Wait (fixed at ~50ms)
		self.flip_it()												# Remove M2

		self.t1_rc.collect()										# Request T1 identity
		self.t2_rc.collect()										# Request T2 identity

		# Save responses
		t1_response = self.t1_rc.keypress_listener.response(rt=False)
		t2_response = self.t2_rc.keypress_listener.response(rt=False)

		# Clear remaining stimuli from screen
		clear()

		# Log trial factors & responses
		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"practicing": str(P.practicing),
			"isoa": self.isoa,
			"isi": self.isi,
			"ttoa": self.ttoa,
			"t1_difficulty": self.t1_difficulty,
			"t1_duration": self.t1_duration,
			"m1_duration": self.m1_duration,
			"t2_duration": self.t2_duration,
			"m2_duration": self.m2_duration,
			"t1_identity": self.t1_identity,
			"t2_identity": self.t2_identity,
			"t1_response": t1_response,
			"t2_response": t2_response
		}

	def trial_clean_up(self):
		# Reset response listeners
		self.t1_rc.keypress_listener.reset()
		self.t2_rc.keypress_listener.reset()

	def clean_up(self):
		pass

	# Clears screen when called
	def flip_it(self):
		fill()
		flip()

	# Presents passed 'it' centre-screen
	def blit_it(self, it):
		fill()
		blit(it, registration=5, location=P.screen_c)
		flip()

	# Presents passed txt centre-screen, hangs until keypress
	def present_txt(self, txt):
		msg = message(txt, align='center', blit_txt=False)
		self.blit_it(msg)
		any_key()

	# Presents fix centre-screen, hangs until keypress
	def present_fixation(self):
		self.blit_it(self.fixation)
		any_key()

	# Request identity response from participants
	def identity_callback(self, target):
		# Request appropriate identity
		identity_request_msg = self.t1_id_request if target == "T1" else self.t2_id_request
		
		fill()
		message(identity_request_msg, location=P.screen_c, registration=5, blit_txt=True)
		flip()

	# Prepares stimulus stream
	def prep_stream(self):
		# Prepare unique masks for each target
		self.t1_mask = self.generate_mask()
		self.t2_mask = self.generate_mask()

		stream_items = {
			't1_target': message(self.t1_identity, align='center', blit_txt=False),
			't1_mask': self.t1_mask,
			't2_target': message(self.t2_identity, align='center', blit_txt=False),
			't2_mask': self.t2_mask
		}

		return stream_items

	# Generates target masks
	def generate_mask(self):
		# Set mask size
		canvas_size = deg_to_px(1)
		# Set cell size
		cell_size = canvas_size / 8 # Mask comprised of 64 smaller cells arranged 8x8
		# Each cell has a black outline
		cell_outline_width = deg_to_px(.01)

		# Initialize canvas to be painted w/ mask cells
		canvas = Image.new('RGBA', [canvas_size, canvas_size], (0,0,0,0))
		surface = aggdraw.Draw(canvas)

		# Initialize pen to draw cell outlines
		transparent_pen = aggdraw.Pen((0,0,0),cell_outline_width)

		# Generate cells
		for row in range(0,15):
			for col in range(0,15):
				# Randomly select colour for each cell
				cell_fill = random.choice([WHITE, BLACK])
				# Brush to apply colour
				fill_brush = aggdraw.Brush(tuple(cell_fill[:3]))
				# Determine cell boundary coords
				top_left = (row * cell_size, col * cell_size)
				bottom_right = ((row+1) * cell_size, (col+1) * cell_size)
				# Create cell
				surface.rectangle(
					(top_left[0], top_left[1], bottom_right[0], bottom_right[1]),
					transparent_pen,
					fill_brush)
		# Apply cells to mask
		surface.flush()

		return np.asarray(canvas)