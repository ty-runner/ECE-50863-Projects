from typing import List
import math
# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================

# My own Implementation
#stronger feedback loop when predicted rates negatively impact buffer occupancy to an extreme degree, and vice versa

# Algorithm that determines the future state of the buffer and "when" the buffer will be full or empty
class ClientMessage:
	"""
	This class will be filled out and passed to student_entrypoint for your algorithm.
	"""
	total_seconds_elapsed: float	  # The number of simulated seconds elapsed in this test
	previous_throughput: float		  # The measured throughput for the previous chunk in kB/s

	buffer_current_fill: float		    # The number of kB currently in the client buffer
	buffer_seconds_per_chunk: float     # Number of seconds that it takes the client to watch a chunk. Every
										# buffer_seconds_per_chunk, a chunk is consumed from the client buffer.
	buffer_seconds_until_empty: float   # The number of seconds of video left in the client buffer. A chunk must
										# be finished downloading before this time to avoid a rebuffer event.
	buffer_max_size: float              # The maximum size of the client buffer. If the client buffer is filled beyond
										# maximum, then download will be throttled until the buffer is no longer full

	# The quality bitrates are formatted as follows:
	#
	#   quality_levels is an integer reflecting the # of quality levels you may choose from.
	#
	#   quality_bitrates is a list of floats specifying the number of kilobytes the upcoming chunk is at each quality
	#   level. Quality level 2 always costs twice as much as quality level 1, quality level 3 is twice as big as 2, and
	#   so on.
	#       quality_bitrates[0] = kB cost for quality level 1
	#       quality_bitrates[1] = kB cost for quality level 2
	#       ...
	#
	#   upcoming_quality_bitrates is a list of quality_bitrates for future chunks. Each entry is a list of
	#   quality_bitrates that will be used for an upcoming chunk. Use this for algorithms that look forward multiple
	#   chunks in the future. Will shrink and eventually become empty as streaming approaches the end of the video.
	#       upcoming_quality_bitrates[0]: Will be used for quality_bitrates in the next student_entrypoint call
	#       upcoming_quality_bitrates[1]: Will be used for quality_bitrates in the student_entrypoint call after that
	#       ...
	#
	quality_levels: int
	quality_bitrates: List[float]
	upcoming_quality_bitrates: List[List[float]]

	# You may use these to tune your algorithm to each user case! Remember, you can and should change these in the
	# config files to simulate different clients!
	#
	#   User Quality of Experience =    (Average chunk quality) * (Quality Coefficient) +
	#                                   -(Number of changes in chunk quality) * (Variation Coefficient)
	#                                   -(Amount of time spent rebuffering) * (Rebuffering Coefficient)
	#
	#   *QoE is then divided by total number of chunks
	#
	quality_coefficient: float
	variation_coefficient: float
	rebuffering_coefficient: float
# ======================================================================================================================


# Your helper functions, variables, classes here. You may also write initialization routines to be called
# when this script is first imported and anything else you wish.

def determine_best_rate(client_message: ClientMessage, calculated_rate: float):
	# If the buffer is full, increase the quality level.
	differences = {}
	for rate in range (client_message.quality_levels):
		difference = abs(client_message.quality_bitrates[rate] - calculated_rate)
		differences[rate] = difference
	min_rate = min(differences, key=differences.get)
	# if min_rate > current_rate:
	# 	print("Increasing rate - transient")
	return min_rate
def next_highest_rate(client_message: ClientMessage, current_rate: int):
	differences = []
	for rate in client_message.quality_bitrates:
		difference = rate - current_rate
		differences.append(difference)
	#print(differences)
	if all(difference < 0 for difference in differences):
		return determine_best_rate(client_message, client_message.previous_throughput)
	else:
		smallest_index = min([i for i, val in enumerate(differences) if val >= 0])
		return smallest_index
	
	
def process(client_message: ClientMessage, previous_rate: int):
	# If the buffer is full, increase the quality level.
	if client_message.buffer_seconds_until_empty >= client_message.buffer_max_size * 0.6:
		return next_highest_rate(client_message, previous_rate)
	# If the buffer is empty, decrease the quality level.
	if client_message.buffer_seconds_until_empty <= client_message.buffer_max_size * 0.3:
		#print("Decreasing rate - steady")
		return 0
	else:
		return next_highest_rate(client_message, previous_rate)
	# If the buffer is neither full nor empty, keep the quality level the same.
last_quality = 0
last_buffer_occupancy = 0
last_bitrate = 0.1
def student_entrypoint(client_message: ClientMessage):
	"""
	Your mission, if you choose to accept it, is to build an algorithm for chunk bitrate selection that provides
	the best possible experience for users streaming from your service.

	Construct an algorithm below that selects a quality for a new chunk given the parameters in ClientMessage. Feel
	free to create any helper function, variables, or classes as you wish.

	Simulation does ~NOT~ run in real time. The code you write can be as slow and complicated as you wish without
	penalizing your results. Focus on picking good qualities!

	Also remember the config files are built for one particular client. You can (and should!) adjust the QoE metrics to
	see how it impacts the final user score. How do algorithms work with a client that really hates rebuffering? What
	about when the client doesn't care about variation? For what QoE coefficients does your algorithm work best, and
	for what coefficients does it fail?

	Args:
		client_message : ClientMessage holding the parameters for this chunk and current client state.

	:return: float Your quality choice. Must be one in the range [0 ... quality_levels - 1] inclusive.
	"""
	global last_quality
	global last_bitrate
	global last_buffer_occupancy
	# IF buffer occupancy < x: we are in startup phase
        #startup = safe
	last_quality = process(client_message, last_bitrate)
	last_bitrate = client_message.quality_bitrates[last_quality]
    # IF buffer occupancy > y: we are in steady state phase
        #steady = aggressive
	# if we are in between, we are in the transient phase
        #transient = either?
	return last_quality
