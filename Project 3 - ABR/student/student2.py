from typing import List

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
class throughput_prediction:
	"""
	Throughput Prediction
	"""
	def __init__(self):
		"""
		Throughput Prediction
		"""
		self.b0 = 0
		self.b1 = 0
		self.num_chunks_list = [1]
		self.num_chunks = 1
		self.difference = last_throughput_difference

	def update_coefficients(self, new_x, new_y):
		mean_x = sum(new_x) / len(new_x)
		mean_y = sum(new_y) / len(new_y)

		old_sum_x = mean_x - self.num_chunks * (self.num_chunks + 1)/ 2
		old_sum_y = sum(new_y) - mean_y / 2
		new_x = [self.num_chunks]
		numerator_b1 = sum([(x - old_sum_x) * (y - old_sum_y) for x, y in zip(new_x, new_y)])
		denominator_b1 = sum([(x - old_sum_x) ** 2 for x in new_x])
		b1 = (self.b1 * denominator_b1 + numerator_b1) / (denominator_b1 + sum([(x - old_sum_x) ** 2 for x in new_x]))
		b0 = mean_y - b1 * mean_x
		return b0, b1
	
	def update(self, new_y):
		new_x = self.num_chunks_list
		self.b0, self.b1 = self.update_coefficients(new_x, [new_y])
		self.num_chunks += 1
		self.num_chunks_list.append(self.num_chunks)
	
	def predict(self, num_predictions):
		future_indices = range(self.num_chunks, self.num_chunks + num_predictions)
		future_predictions = [self.b0 + self.b1 * i for i in future_indices]
		return future_predictions

def initialize_prediction_model():
	global prediction_model
	prediction_model = throughput_prediction()

def MPC(client_message: ClientMessage, last_bitrate: float, estimated_throughput: float, last_buffer_occupancy) -> float:
	"""
	MPC function
	"""
	# #dk(Rk) / C(k)
	# expected_download_time = last_bitrate / estimated_throughput
	# #print(f"Expected Download Time: {expected_download_time}")
	# #Equation 4 of paper
	# delta_t = ((client_message.buffer_seconds_until_empty - expected_download_time) + client_message.buffer_seconds_per_chunk - client_message.buffer_max_size)
	# delta_t = max(0, delta_t)
	# #print(f"Delta_t: {delta_t}")
	# #Equation 1 of paper
	# wait_time = delta_t + expected_download_time
	# #print(f"Wait Time: {wait_time}")
	# #Equation 2 of paper
	# return 1, 1
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
	if predicted_rebuffer_time > 0 and predicted_quality > 0:
		predicted_quality -= 1

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
	if prediction_model is None:
		initialize_prediction_model()
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
	if client_message.total_seconds_elapsed < 1:
		# startup phase
		for throughput in past_throughputs:
			#print(f"Throughput: {throughput}")
			prediction_model.update(throughput)
		C = prediction_model.predict(5)
		# MPC predict for startup time and Bitrate
		R, predicted_quality = MPC(client_message, last_bitrate, C[0], last_buffer_occupancy)
		# start playback after startup time seconds
	else:
		# playback has started
		prediction_model.update(client_message.previous_throughput)
		C = prediction_model.predict(5)
		# MPC predict for current time and Bitrate
		R, predicted_quality = MPC(client_message, last_bitrate, C[0], last_buffer_occupancy)
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
	prediction_model.difference = last_throughput_difference
	previous_throughput_est = C[0]
	#print(f"Last Throughput Difference: {last_throughput_difference}")
	return predicted_quality
