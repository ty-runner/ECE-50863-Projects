import numpy as np
import os
import configparser
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from tensorflow.keras.preprocessing.sequence import pad_sequences


# Config parser
VIDEO_HEADING	   = 'video'
CHUNK_LENGTH		= 'chunk_length'
CLIENT_BUFF_SIZE	= 'client_buffer_size'

QUALITY_HEADING	 = 'quality'
QUALITY_LEVELS	  = 'quality_levels'
BASE_CHUNK_SIZE = 'base_chunk_size'
QUAL_COEF		   = 'quality_coefficient'
BUF_COEF			= 'rebuffering_coefficient'
SWITCH_COEF		 = 'variation_coefficient'

THROUGHPUT_HEADING  = 'throughput'

CHUNK_SIZE_RATIOS_HEADING  = 'chunk_size_ratios'
CHUNK_SIZE_RATIOS		 = 'chunk_size_ratios'
def read_test(config_path: str, print_output: bool):
	"""
	Reads and loads parameters from config_path
	Args:
		config_path : .ini file to read
		print_output : Whether to print output
	:return:
		Tuple containing the NetworkTrace, Scorecard, SimBuffer, a list of chunk quality bitrates,
		and the chunk duration. The chunk quality options are formatted as a list of lists. e.g.
		chunk_qualities[3][1] = number of bytes for chunk index 3, quality index 1.
	"""
	try:
		if print_output: print(f'\nLoading test file {config_path}.')
		cfg = configparser.RawConfigParser(allow_no_value=True, inline_comment_prefixes='#')
		cfg.read(config_path)

		chunk_length = float(cfg.get(VIDEO_HEADING, CHUNK_LENGTH))
		base_chunk_cost = float(cfg.get(VIDEO_HEADING, BASE_CHUNK_SIZE))
		client_buffer_size = float(cfg.get(VIDEO_HEADING, CLIENT_BUFF_SIZE))
		if print_output: print(f'\tLoaded chunk length {chunk_length} seconds, base cost {base_chunk_cost} megabytes.')

		quality_levels = int(cfg.get(QUALITY_HEADING, QUALITY_LEVELS))
		if print_output: print(f'\tLoaded {quality_levels} quality levels available.')

		quality_coefficient = float(cfg.get(QUALITY_HEADING, QUAL_COEF))
		rebuffering_coefficient = float(cfg.get(QUALITY_HEADING, BUF_COEF))
		variation_coefficient = float(cfg.get(QUALITY_HEADING, SWITCH_COEF))
		if print_output: print(f'\tLoaded {quality_coefficient} quality coefficient,'
							   f' {rebuffering_coefficient} rebuffering coefficient,'
							   f' {variation_coefficient} variation coefficient.')

		throughputs = dict(cfg.items(THROUGHPUT_HEADING))
		throughputs = [(float(time), float(throughput)) for time, throughput in throughputs.items()]
		if print_output: print(f'\tLoaded {len(throughputs)} different throughputs.')

		chunks = cfg.get(CHUNK_SIZE_RATIOS_HEADING, CHUNK_SIZE_RATIOS)
		chunks = list(float(x) for x in chunks.split(',') if x.strip())
		chunk_qualities = [[c * (2**i) * base_chunk_cost for i in range(quality_levels)] for c in chunks]
		if print_output: print(f'\tLoaded {len(chunks)} chunks. Total video length is {len(chunks) * chunk_length} seconds.')


		if print_output: print(f'\tDone reading config!\n')

		return chunk_qualities, chunk_length, throughputs

	except:
		print('Exception reading config file!')
		import traceback
		traceback.print_exc()
		exit()
# Function to prepare data
def prepare_data(config_files_dir):
	config_files = os.listdir(config_files_dir)
	data_list = []
	for config_file in config_files:
		if config_file.endswith(".ini"):
			chunk_qualities, chunk_length, throughputs = read_test(config_files_dir + config_file, print_output=False)
			print(f"Loaded data from {config_file}")
			print(f"Chunk qualities: {throughputs}")
			data_list.append(np.array(throughputs))
	with open('throughputs.txt', 'w') as file:
		for data in data_list:
			file.write(str(data) + '\n')
	return data_list




# Sample usage
config_files_dir = "../tests/"
data = prepare_data(config_files_dir)
padded_data = pad_sequences(data, maxlen=211, padding='post')
X = np.array(data)
y = np.array(data)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
train_predictions = model.predict(X_train)
val_predictions = model.predict(X_val)
train_mse = mean_squared_error(y_train, train_predictions)
val_mse = mean_squared_error(y_val, val_predictions)
print(f"Train MSE: {train_mse}")
print(f"Validation MSE: {val_mse}")
