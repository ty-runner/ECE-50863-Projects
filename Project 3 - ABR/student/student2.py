from typing import List
import statistics
# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================

# RobustMPC Implementation

class ClientMessage:
	"""
	This class will be filled out and passed to student_entrypoint for your algorithm.
	"""
	total_seconds_elapsed: float	  # The number of simulated seconds elapsed in this test
	previous_throughput: float		  # The measured throughput for the previous chunk in kB/s

	#buffer_current_fill: float		    # The number of kB currently in the client buffer
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
past_throughputs = [0.5, 1, 0.5, 1]
last_bitrate = 0
last_buffer_occupancy = 0
last_throughput_difference = 0
prediction_model = None
previous_throughput_est = 0

def harmonic_mean(past_throughputs):
	num_of_entries = min(3, len(past_throughputs))
	#print(num_of_entries / sum([1 / throughput for throughput in past_throughputs[:num_of_entries]]))
	return statistics.harmonic_mean(past_throughputs[:num_of_entries])
def MPC(client_message: ClientMessage, last_bitrate: float, estimated_throughput: float, last_buffer_occupancy) -> float:
	"""
	MPC function
	"""
	alpha = 0.9
	beta = 0.1
	predicted_buffer_occupancy = last_buffer_occupancy - (last_bitrate / estimated_throughput) + client_message.buffer_seconds_per_chunk
	expected_download_time = last_bitrate / estimated_throughput
	predicted_rebuffer_time = max(0, client_message.buffer_seconds_until_empty - last_buffer_occupancy / estimated_throughput)
	# print(f"Predicted rebuffer time: {predicted_rebuffer_time}")
	# if predicted_rebuffer_time > 0:
	# 	return client_message.quality_bitrates[0], 0
	# print(f"Predicted Buffer Occupancy: {predicted_buffer_occupancy}")
	# print(f"Actual buffer occupancy: {client_message.buffer_seconds_until_empty}")
	predicted_quality = int((alpha * estimated_throughput + beta * predicted_buffer_occupancy) / client_message.quality_bitrates[0])
	predicted_quality = min(max(predicted_quality, 0), client_message.quality_levels - 1)
	predicted_quality = int(predicted_quality)
	# if predicted_rebuffer_time > 0 and predicted_quality > 0:
	# 	predicted_quality -= 1
	
	selected_bitrate = client_message.quality_bitrates[predicted_quality]
	return selected_bitrate, predicted_quality

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
	global past_throughputs
	global last_bitrate
	global last_buffer_occupancy
	global prediction_model
	global last_throughput_difference
	global previous_throughput_est
	# if in startup phase then:
	# 	C[tk, tk+N] = ThroughputPRediction(C[t1,tk])
	# 	R, T = MPC(C, R[t1,tk])
	# 	start playback after T seconds
	# else if playback has started then:
	# 	C = ThroughputPRediction(C[t1,tk])
	# 	R = MPC(R[t1,tk], Bk, C[tk, tk+N])
	# end if
	# Download chunk k with bitrate Rk, wait till finished
	# end for
	if client_message.total_seconds_elapsed < 10:
		# startup phase
		C = harmonic_mean(past_throughputs)
		# MPC predict for startup time and Bitrate
		R, predicted_quality = MPC(client_message, last_bitrate, C, last_buffer_occupancy)
		# start playback after startup time seconds
	else:
		C = harmonic_mean(past_throughputs)
		# MPC predict for current time and Bitrate
		R, predicted_quality = MPC(client_message, last_bitrate, C, last_buffer_occupancy)
	if (client_message.previous_throughput != 0):
		past_throughputs.append(client_message.previous_throughput)
	else:
		past_throughputs.append(0.5)
	last_bitrate = R
	last_buffer_occupancy = client_message.buffer_seconds_until_empty
	#print(f"Predicted Quality: {predicted_quality}, Selected Bitrate: {R}")
	#print(f"Difference between predicted throughput and actual throughput: {abs(client_message.previous_throughput - C)}")
	#print(f"Upcoming Quality Bitrates: {client_message.upcoming_quality_bitrates}")
	#print(f"C0: {C[0]}")
	#print(f"Previous guess {previous_throughput_est}")
	last_throughput_difference = previous_throughput_est - client_message.previous_throughput
	previous_throughput_est = C
	#print(f"Last Throughput Difference: {last_throughput_difference}")
	#print(f"Predicted Quality: {predicted_quality}")
	return predicted_quality
