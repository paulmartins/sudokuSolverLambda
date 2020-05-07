# To run:
# $ python lambda_function_local.py sudoku_01.txt 

import lambda_function
import sys
import numpy as np

if __name__ == '__main__':

	if len(sys.argv) > 1:
		file_location = sys.argv[1].strip()
		with open(file_location, 'r') as input_data_file:
			input_data = input_data_file.read()
		lines = input_data.split('\n')
		SUDOKU_SIZE = len(lines)
		input_matrix = np.matrix([np.array(l.split(), dtype=int) for l in lines])
		print(lambda_function.solve_sudoku([input_matrix])[0])
