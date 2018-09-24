# -*- coding: utf-8 -*-

__author__ = "Brett Feltmate"

import klibs
from klibs import P
from klibs.KLConstants import STROKE_INNER, TK_S, NA, RC_COLORSELECT, RC_KEYPRESS
from klibs.KLUtilities import *
from klibs.KLKeyMap import KeyMap
from klibs.KLUserInterface import any_key, ui_request
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLGraphics.KLDraw import *
from klibs.KLGraphics.colorspaces import const_lum as colors
from klibs.KLResponseCollectors import ResponseCollector
from klibs.KLEventInterface import TrialEventTicket as ET
from klibs.KLCommunication import message
from klibs.KLTime import CountDown, Stopwatch
# Import required external libraries
import sdl2
import time
import random

# Define some useful constants
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)
GRAY = (127,127,127,255)

IDENTITY = "identity"
COLOUR = "colour"

letters = ['A', 'B', 'C', 'D', 'E',
           'F', 'G', 'H', 'I', 'J',
           'K', 'L', 'M', 'N', 'P',
           'Q', 'R', 'S', 'T', 'U',
           'V', 'W', 'X', 'Y', 'Z']

numbers = ['1', '2', '3', '4', '5',
                '6', '7', '8', '9']


class ABColour_NoSwitch(klibs.Experiment):

	def setup(self):
		# Stimulus sizes
		fix_thickness = deg_to_px(0.1)
		fix_size = deg_to_px(0.6)
		wheel_size = int(P.screen_y * 0.75) 
		cursor_size = deg_to_px(1)
		cursor_thickness = deg_to_px(0.3)
		target_size = deg_to_px(2)
		
		# Make this a variable to be assigned & runtime
		self.item_duration = 0.120

		# Stimulus drawbjects
		self.fixation = Asterisk(fix_size,fix_thickness,fill=WHITE)
		self.t1_wheel = ColorWheel(diameter=wheel_size)
		self.t2_wheel = ColorWheel(diameter=wheel_size)
		self.cursor = Annulus(cursor_size,cursor_thickness,fill=BLACK)

		# Colour ResponseCollector needs to be passed an object whose fill (colour)
		# is that of the target colour. W/n trial_prep(), these dummies will be filled
		# w/ the target colour and then passed to their ResponseCollectors, respectively.
		self.t1_dummy = Ellipse(width=1)
		self.t2_dummy = Ellipse(width=1)

		# Target & distractor text styles
		self.txtm.add_style(label='T1Col',font_size=target_size)
		self.txtm.add_style(label='T2Col',font_size=target_size)
		self.txtm.add_style(label='stream', font_size=target_size)

		# Experiment messages
		self.anykey_txt = "{0}\nPress any key to continue."
		self.t1_id_request = "What number was the first target you saw?\n"
		self.t2_id_request = "What number was the second target you saw?\n"
		self.identity_instruct = "\nIn this block, you will be asked to report which two numbers were presented."
		self.colour_instruct = "\nIn this block, you will be asked to report which two colours were presented."

		# Initialize ResponseCollectors
		self.t1_identity_rc = ResponseCollector(uses=RC_KEYPRESS)
		self.t2_identity_rc = ResponseCollector(uses=RC_KEYPRESS)

		self.t1_colouring_rc = ResponseCollector(uses=RC_COLORSELECT)
		self.t2_colouring_rc = ResponseCollector(uses=RC_COLORSELECT)

		# Initialize ResponseCollector Keymaps
		self.keymap = KeyMap(
			'identity_response',
			['1','2','3','4','5','6','7','8','9'],
			['1','2','3','4','5','6','7','8','9'],
			[sdl2.SDLK_1,sdl2.SDLK_2,sdl2.SDLK_3,
			sdl2.SDLK_4,sdl2.SDLK_5,sdl2.SDLK_6,
			sdl2.SDLK_7,sdl2.SDLK_8,sdl2.SDLK_9]
		)

		# Pre-render letters & digits
		self.letters_rendered = {}
		for letter in letters:
			self.letters_rendered[letter] = message(letter, style='stream',align='center', blit_txt=False)

		self.numbers_rendered = {}
		for number in numbers:
			self.numbers_rendered[number] = message(number, style='stream',align='center',blit_txt=False)

		# Insert practice blocks (one for each response type)
		if P.run_practice_blocks:
			self.insert_practice_block(block_nums=1, trial_counts=P.trials_per_practice_block)
			self.insert_practice_block(block_nums=2, trial_counts=P.trials_per_practice_block)

		self.block_type = IDENTITY


	def block(self):
		# Present block progress
		block_txt = "Block {0} of {1}".format(P.block_number, P.blocks_per_experiment)
		progress_txt = self.anykey_txt.format(block_txt)

		if P.practicing: 
			progress_txt += "\n(This is a practice block)"

		progress_msg = message(progress_txt, align='center', blit_txt=False)

		fill()
		blit(progress_msg,5,P.screen_c)
		flip()
		any_key()

		# Inform as to block type
		if self.block_type == COLOUR:
			block_type_txt = self.anykey_txt.format(self.colour_instruct)
		else:
			block_type_txt = self.anykey_txt.format(self.identity_instruct)

		block_type_msg = message(block_type_txt, align='center', blit_txt=False)

		fill()
		blit(block_type_msg,5,P.screen_c)
		flip()
		any_key()

	def setup_response_collector(self):
		# Configure identity collector
		self.t1_identity_rc.terminate_after = [10, TK_S] # Waits 10s for response
		self.t1_identity_rc.display_callback = self.identity_callback # Continuously draw images to screen	
		self.t1_identity_rc.display_kwargs = {'target':"T1"} # Passed as arg when identity_callback() is called
		self.t1_identity_rc.keypress_listener.key_map = self.keymap # Assign key mappings
		self.t1_identity_rc.keypress_listener.interrupts = True # Terminates listener after valid response

		self.t2_identity_rc.terminate_after = [10, TK_S] 
		self.t2_identity_rc.display_callback = self.identity_callback
		self.t2_identity_rc.display_kwargs = {'target':"T2"}
		self.t2_identity_rc.keypress_listener.key_map = self.keymap 
		self.t2_identity_rc.keypress_listener.interrupts = True 

		# Configure colour collector
		# Because colours are randomly selected on a trial by trial basis
		# most properties of colouring_rc need to be assigned w/n trial_prep()
		self.t1_colouring_rc.terminate_after = [10, TK_S]
		self.t2_colouring_rc.terminate_after = [10, TK_S]

	def trial_prep(self):
		# Prepare colour wheels
		self.t1_wheel.rotation = random.randrange(0,360) # Randomly rotate wheel to prevent location biases
		self.t1_wheel.render()

		self.t2_wheel.rotation = random.randrange(0,360) # Randomly rotate wheel to prevent location biases
		self.t2_wheel.render()

		# Prepare T1 & T2
		self.t1_identity = random.sample(numbers, 1)[0] # Select & assign identity
		self.t1_colour = self.t1_wheel.color_from_angle(random.randrange(0,360)) # Select & assign colouring
		self.t1_time = random.sample(range(5), 1)[0] + 5 # Select T1 stream position, no earlier than the 5th item
	

		self.t2_identity = random.sample(numbers,1)[0]
		self.t2_colour = self.t2_wheel.color_from_angle(random.randrange(0,360))
		self.t2_time = self.t1_time + self.lag # Lag: # of items interspacing the two targets (can be 1-8)
		

		while self.t1_identity == self.t2_identity: # Ensure that T1 & T2 identities are unique
			self.t2_identity = random.sample(numbers,1)[0]

		while self.t1_colour == self.t2_colour: # Similarly, colouring
			self.t2_colour = self.t2_wheel.color_from_angle(random.randrange(0,360))

		# Dummy objects to serve as reference point when calculating response error
		self.t1_dummy.fill = self.t1_colour
		self.t2_dummy.fill = self.t2_colour

		self.t1_colouring_rc.display_callback = self.wheel_callback
		self.t1_colouring_rc.display_kwargs = {'wheel': self.t1_wheel}

		self.t1_colouring_rc.color_listener.set_wheel(self.t1_wheel) # Set generated wheel as wheel to use
		self.t1_colouring_rc.color_listener.set_target(self.t1_dummy)

		self.t2_colouring_rc.display_callback = self.wheel_callback
		self.t2_colouring_rc.display_kwargs = {'wheel': self.t2_wheel}

		self.t2_colouring_rc.color_listener.set_wheel(self.t2_wheel)
		self.t2_colouring_rc.color_listener.set_target(self.t2_dummy)

		
		# Prepare stream according to response block (Identity | Colouring)
		self.rsvp_stream = self.prep_stream(self.block_type) 

		# Initialize EventManager
		# Stream begins 1000ms after fixation
		self.evm.register_ticket(ET('stream_on',1000))

	def trial(self):

		# Hide cursor during trial
		hide_mouse_cursor()
		
		# Present fixation & wait 1s before presenting RSVP stream
		self.present_fixation()
		while self.evm.before('stream_on', True):
			pass

		# Present RSVP stream
		self.present_stream()

		# For 'identity' blocks, request targets' numerical identity
		if self.block_type == IDENTITY:
			# Collect responses
			self.t1_identity_rc.collect()
			self.t2_identity_rc.collect()

			# Assign to return variables
			t1_id_response, t1_id_rt = self.t1_identity_rc.keypress_listener.response()
			t2_id_response, t2_id_rt = self.t2_identity_rc.keypress_listener.response()

			t1_response_err, t1_response_err_rt, t2_response_err, t2_response_err_rt = ['NA','NA','NA','NA']

		# For 'colour' blocks, request targets' colouring
		else:
			self.t1_colouring_rc.collect()
			self.t2_colouring_rc.collect()

			t1_response_err, t1_response_err_rt = self.t1_colouring_rc.color_listener.response()
			t2_response_err, t2_response_err_rt = self.t2_colouring_rc.color_listener.response()

			t1_id_response, t1_id_rt, t2_id_response, t2_id_rt = ['NA','NA','NA','NA']

		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"block_type": self.block_type,
			"t1_time": self.t1_time,
			"t2_time": self.t2_time,
			"lag": self.lag,
			"t1_identity": self.t1_identity,
			"t2_identity": self.t2_identity,
			"t1_identity_response": t1_id_response,
			"t1_identity_rt": t1_id_rt,
			"t2_identity_response": t2_id_response,
			"t2_identity_rt": t2_id_rt,
			"t1_colour": self.t1_colour,
			"t2_colour": self.t2_colour,
			"t1_ang_err": t1_response_err,
			"t1_ang_err_rt": t1_response_err_rt,
			"t2_ang_err": t2_response_err,
			"t2_ang_err_rt": t2_response_err_rt,
			"t1_wheel_rotation": self.t1_wheel.rotation,
			"t2_wheel_rotation": self.t2_wheel.rotation
		}

		# Clear remaining stimuli from screen
		clear()

	def trial_clean_up(self):
		# Reset ResponseCollectors
		self.t1_colouring_rc.color_listener.reset()
		self.t2_colouring_rc.color_listener.reset()

		self.t1_identity_rc.keypress_listener.reset()
		self.t2_identity_rc.keypress_listener.reset()
			
		# Switch block type
		if not P.practicing:
			if P.trial_number == P.trials_per_block:
				if P.block_number < P.blocks_per_experiment:
					if self.block_type == IDENTITY:
						self.block_type = COLOUR
					else:
						self.block_type = IDENTITY
		else:
			if P.trial_number == P.trials_per_practice_block:
					if self.block_type == IDENTITY:
						self.block_type = COLOUR
					else:
						self.block_type = IDENTITY
		
		if P.trial_number == P.trials_per_block:
			break_txt = self.anykey_txt.format("Good work! Take a break")
			break_msg = message(break_txt,align='center',blit_txt=False)

			fill()
			blit(break_msg,registration=5,location=P.screen_c)
			flip()
			any_key()

	def clean_up(self):
		# Inform Ss that they have completed the experiment
		all_done_txt = "Whew! You're all done!\nPlease buzz the researcher to let them know."
		all_done_msg = message(all_done_txt, align="center", blit_txt=False)

		fill()
		blit(all_done_msg,5,P.screen_c)
		flip()
		any_key()

	def present_fixation(self):
		fill()
		blit(self.fixation, location=P.screen_c, registration=5)
		flip()
	

	def wheel_callback(self, wheel):
		fill()
		# Hide cursor during selection phase
		hide_mouse_cursor()
		# Present appropriate wheel
		if wheel == self.t1_wheel:
			blit(self.t1_wheel, registration=5, location=P.screen_c)
		else:
			blit(self.t2_wheel, registration=5, location=P.screen_c)
		# Present annulus drawbject as cursor
		blit(self.cursor,registration=5,location=mouse_pos())
		flip()

	def identity_callback(self,target):
		# Request appropriate identity
		identity_request_msg = self.t1_id_request if target == "T1" else self.t2_id_request
		
		fill()
		message(identity_request_msg, location=P.screen_c, registration=5, blit_txt=True)
		flip()

	def prep_stream(self, block):
		# To be populated & returned
		stream_items = []

		# Set font colouring for targets (only used w/n COLOUR blocks)
		self.txtm.styles['T1Col'].color = self.t1_colour
		self.txtm.styles['T2Col'].color = self.t2_colour

		# For IDENTITY streams, targets=digits & distractors=letters. 
		# All are uniformly coloured (gray)
		if block == IDENTITY:
			# Stream length is such that 6 items are always presented subsequent to T2
			for i in range(0, self.t2_time+6):
				# Insert targets @ their respective positions
				if i == self.t1_time:
					stream_items.append(message(self.t1_identity, align='center', style='stream',blit_txt=False))
				elif i == self.t2_time:
					stream_items.append(message(self.t2_identity, align='center', style='stream',blit_txt=False))
				# Populate remaining positions w/ distractors (randomly sampled)
				else:
					stream_items.append(random.choice(self.letters_rendered.values()))
		# For COLOUR streams, targets & distractors are digits. 
		# Targets are randomly coloured, distractors are gray
		else:


			for i in range(0, self.t2_time+6):
				if i == self.t1_time:
					stream_items.append(message(self.t1_identity, align='center', style='T1Col',blit_txt=False))
				elif i == self.t2_time:
					stream_items.append(message(self.t2_identity, align='center', style='T2Col',blit_txt=False))
				else:
					stream_items.append(random.choice(self.numbers_rendered.values()))

		# Return stream

		return stream_items

	def present_stream(self):
		# Each stream item presented for a pre-specified duration
		cd = CountDown(self.item_duration)
		sw = Stopwatch()
		for item in self.rsvp_stream:
			cd.reset()
			sw.reset()
			fill()
			blit(item, registration=5, location=P.screen_c)
			flip()

			#print(cd.elapsed)
			while cd.counting():
				ui_request() 
			print(sw.elapsed())
			sw.reset()