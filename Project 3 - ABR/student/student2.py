from typing import List

# Adapted from code by Zach Peats

# ======================================================================================================================
# Do not touch the client message class!
# ======================================================================================================================

# RobustMPC Implementation

#  High level overview of workflow:
# Initialize
# for k = 1 to K do:
# 	if player is in startup phase then:
# 		ThroughputEstimation
# 		MPC predict for startup time and Bitrate
# 		start playback after startup time seconds
# 	else if playback has started then:
# 		ThroughputEstimation
# 		MPC predict for current time and Bitrate
# 	end if
# 	Download chunk k with bitrate Rk, wait till finished
# end for
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
past_throughputs = []
last_bitrate = 0
last_buffer_occupancy = 0
def throughput_prediction(client_message: ClientMessage, past_throughputs: List[float]):
	"""
	Throughput prediction function
	"""
	# if past_throughputs is empty then return the previous throughput
	if len(past_throughputs) == 0:
		return 0.5

	# if past_throughputs is not empty then return the average throughput
	#print(f"Past Throughputs: {past_throughputs}")
	return sum(past_throughputs) / len(past_throughputs)
	
def MPC(client_message: ClientMessage, last_bitrate: float, estimated_throughput: float, last_buffer_occupancy) -> float:
    """
    MPC function for selecting bitrate of next chunk
    
    Args:
        client_message (ClientMessage): Object containing client parameters
        last_bitrate (float): Bitrate of the last downloaded chunk
        estimated_throughput (float): Estimated throughput based on past data
        
    Returns:
        float: Selected bitrate for the next chunk
    """
    # Constants for MPC control
    alpha = 0.5  # Weight for throughput estimation
    beta = 0.5   # Weight for buffer occupancy
    
    # Calculate predicted buffer occupancy after downloading next chunk
    predicted_buffer_occupancy = client_message.buffer_seconds_until_empty - last_bitrate * client_message.buffer_seconds_per_chunk + estimated_throughput
    
    # Calculate predicted rebuffering time (if any)
    predicted_rebuffer_time = max(0, client_message.buffer_seconds_until_empty - last_buffer_occupancy / estimated_throughput)
    
    # Calculate predicted quality level
    predicted_quality = int((alpha * estimated_throughput + beta * predicted_buffer_occupancy) / client_message.quality_bitrates[0])
    
    # Adjust predicted quality to ensure it's within the available quality levels
    predicted_quality = min(max(predicted_quality, 0), client_message.quality_levels - 1)
    
    # Select bitrate based on predicted quality level
    selected_bitrate = client_message.quality_bitrates[int(predicted_quality)]
    #print(f"Predicted Quality: {predicted_quality}, Selected Bitrate: {selected_bitrate}")
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
		C = throughput_prediction(client_message, past_throughputs)
		#print(f"Throughput Prediction: {C}")
		# MPC predict for startup time and Bitrate
		R, predicted_quality = MPC(client_message, last_bitrate, C, last_buffer_occupancy)
		# start playback after startup time seconds
	else:
		# playback has started
		C = throughput_prediction(client_message, past_throughputs)
		#print(f"Throughput Prediction: {C}")
		# MPC predict for current time and Bitrate
		R, predicted_quality = MPC(client_message, last_bitrate, C, last_buffer_occupancy)
	if (client_message.previous_throughput != 0):
		past_throughputs.append(client_message.previous_throughput)
	else:
		past_throughputs.append(0.1)
	last_bitrate = R
	last_buffer_occupancy = client_message.buffer_seconds_until_empty
	#print(f"Predicted Quality: {predicted_quality}, Selected Bitrate: {R}")
	return predicted_quality
