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
	
def estimate_throughput(client_message: ClientMessage, past_throughputs: List[float]):
	# Estimate the throughput for the next chunk.
	# Use the harmonic mean of the past throughputs.
	throughputs = past_throughputs[-5:]
	sum_inverse_throughputs = 0
	count_nonzero_throughputs = 0

	for throughput in throughputs:
		if throughput != 0:
			sum_inverse_throughputs += 1 / throughput
			count_nonzero_throughputs += 1
	if count_nonzero_throughputs > 0:
		est_throughput = count_nonzero_throughputs / sum_inverse_throughputs
	else:
		est_throughput = 0.5
	return est_throughput

def buffer_based_decision(client_message: ClientMessage, est_throughput: float, process_flag: int):
	if process_flag >= 0 and process_flag <= 2:
		download_times = []
		differences = []
		for quality in range(client_message.quality_levels):
				download_time = (client_message.quality_bitrates[quality]) / (est_throughput)
				download_times.append(download_time)
		if process_flag == 0:
			closest_value = min(download_times, key=lambda x:abs(x - 0.75))
			return download_times.index(closest_value)
		if process_flag == 1:
			return client_message.quality_levels - 1

def variation_control(last_quality: int, current_quality: int):
	#Make sure if there is a change in quality, it is only 1 tier up or down
	if abs(last_quality - current_quality) > 1:
		if last_quality > current_quality:
			return last_quality - 1
		else:
			return last_quality + 1
	return current_quality
last_quality = 0
last_buffer_occupancy = 0
last_bitrate = 1
past_throughputs = []
buffer_deltas = []
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
	global past_throughputs
	global buffer_deltas 
	# Buffer based rate control with some predictive elements
	
	"""
	Make each quality decision based on the following:
	- Estimated throughput: Harmonic mean on BBA?
	- Current buffer occupancy
	- How much time is left in the session
	- Upcoming qualities
	"""
	lower_reservior = client_message.buffer_max_size * 0.3
	upper_reservior = client_message.buffer_max_size * 0.6
	past_throughputs.append(client_message.previous_throughput)
	est_throughput = estimate_throughput(client_message, past_throughputs)
	average_throughput = sum(past_throughputs) / len(past_throughputs)
	#print(f"Avg throughput: {average_throughput}")
	#we should scale this based on the average throughput
 
	if average_throughput > 1.6:
		lower_reservior = client_message.buffer_max_size * 0.15
		upper_reservior = client_message.buffer_max_size * 0.3

	if client_message.buffer_seconds_until_empty <= lower_reservior:
		process_flag = 0
	elif client_message.buffer_seconds_until_empty >= upper_reservior:
		process_flag = 1
	else:
		process_flag = 0
	quality = buffer_based_decision(client_message, est_throughput, process_flag)
	buffer_deltas.append(client_message.buffer_seconds_until_empty - last_buffer_occupancy)
	last_buffer_occupancy = client_message.buffer_seconds_until_empty

	worst_loss = min(buffer_deltas)
	if worst_loss == 0:
		worst_loss = 1
	if worst_loss < 0:
		#print("Increasing rate - steady")
		worst_loss = abs(worst_loss)
		if (client_message.buffer_seconds_until_empty > (240 - client_message.total_seconds_elapsed)):
			quality = 2
	quality = variation_control(last_quality, quality)
	last_quality = quality
	# print(f"Buffer occupancy: {client_message.buffer_seconds_until_empty}")
	# print(f"Quality: {quality}")
	return quality
