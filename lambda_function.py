import boto3
import os
import sys
import uuid
import numpy as np

from urllib.parse import unquote_plus
from collections import namedtuple
from operator import attrgetter

s3_client = boto3.client('s3')

Grid = namedtuple("Grid", ['grid', 'objective'])

global SUDOKU_SIZE
SUDOKU_SIZE = 9

def numberIs(i, cube_solution):
	if i > 0:
		# return the matrix where number i is located
		return cube_solution[i-1]
	elif i == 0:
		# return the matrix to say where the unknowed numbers are
		return np.sum(cube_solution, axis=0)
	else:
		return f'Error: Pleased enter a number between 0 and {SUDOKU_SIZE}'

def calculateObjective(current_input_matrix):
	return 100*np.sum(current_input_matrix>0)/(SUDOKU_SIZE**2)

def propagateConstraint(current_input_matrix):
	cube_solution = np.zeros((SUDOKU_SIZE, SUDOKU_SIZE, SUDOKU_SIZE)).astype(int)
	for idx, row in enumerate(current_input_matrix):
		for i in range(SUDOKU_SIZE):
			cube_solution[i][idx] = np.array(i+1 == row, dtype=int)
	cube_constraint = np.zeros((SUDOKU_SIZE, SUDOKU_SIZE, SUDOKU_SIZE)).astype(int)
	for idx, mat in enumerate(cube_solution):
		# mat = matrix filled with 1 if it has number idx
		for i in range(SUDOKU_SIZE):
			# line constraint
			if 1 in mat[i]:
				cube_constraint[idx][i] = np.ones(SUDOKU_SIZE)
			# row constraint
			if 1 in mat[:,i]:
				cube_constraint[idx][:,i] = np.ones(SUDOKU_SIZE)
			# small square constraint
			sqrt_size = int(np.sqrt(SUDOKU_SIZE))
			row_s = int(sqrt_size*np.floor(i/sqrt_size))
			row_e = int(sqrt_size*np.floor(i/sqrt_size)+sqrt_size)
			col_s = int(sqrt_size*i-SUDOKU_SIZE*np.floor(i/sqrt_size))
			col_e = int(sqrt_size*i-SUDOKU_SIZE*np.floor(i/sqrt_size)+sqrt_size)
			if 1 in np.concatenate(mat[row_s:row_e, col_s:col_e]):
				cube_constraint[idx][row_s:row_e, col_s:col_e] = np.ones((sqrt_size,sqrt_size))
	return cube_constraint, cube_solution

def findNextGrids(cube_constraint, cube_solution, current_input_matrix):
	# check which numbers are fully constraint (8) and still unknown
	new_number_posistion = np.logical_and(np.sum(cube_constraint, axis=0)==(SUDOKU_SIZE-1), numberIs(0, cube_solution)==0)
	# if at least one is fully constrained, fill the grid with its value
	if True in new_number_posistion:
		# find the new number values
		new_numbers = np.zeros((SUDOKU_SIZE,SUDOKU_SIZE))
		for idx, mat in enumerate(cube_constraint):
			new_numbers += (idx+1)*(1-mat)
		# only fill one number at a time, longer but avoid 16x16 empty grid issue
		# where last 2 lines are filled simultaneously
		single_max_index = np.argmax(new_number_posistion)
		single_line_idx = int(single_max_index/SUDOKU_SIZE)
		single_col_idx = single_max_index % SUDOKU_SIZE
		current_input_matrix[single_line_idx,single_col_idx] = new_numbers[single_line_idx,single_col_idx]
		# to fill multiple numbers in one go, but need to make sure those 
		# obeys the sudoku rules
		# current_input_matrix[new_number_posistion] = new_numbers[new_number_posistion]
		grid_output = [current_input_matrix]
	# if non are fully constrained, find all the possibilities and add them to the list
	else:
		sub_cube_constraint = np.sum(cube_constraint, axis=0)
		mask_filter = np.logical_and(sub_cube_constraint<(SUDOKU_SIZE-1), numberIs(0, cube_solution)==0)
		sub_cube_constraint[np.logical_not(mask_filter)] = 0
		max_idx = np.argmax(sub_cube_constraint)
		best_line_idx = int(max_idx/SUDOKU_SIZE)
		best_col_idx = max_idx % SUDOKU_SIZE
		# find possible values for that number
		possible_values = [idx+1 for idx,c in enumerate(cube_constraint) if c[best_line_idx, best_col_idx]==0]
		if possible_values == []:
			grid_output=[]
		else:
			# return all the possible grids
			grid_output = [current_input_matrix.copy() for i in possible_values]
			for idx, value in enumerate(possible_values):
				grid_output[idx][best_line_idx, best_col_idx] = value
	return [Grid(grid=g, objective=calculateObjective(g)) for g in grid_output]


def solve_sudoku(file_location):
	with open(file_location, 'r') as input_data_file:
		input_data = input_data_file.read()

	lines = input_data.split('\n')
	SUDOKU_SIZE = len(lines)
	input_matrix = np.matrix([np.array(l.split(), dtype=int) for l in lines])
	input_grid = [Grid(grid=input_matrix, objective=calculateObjective(input_matrix))]
	counter = 0
	while len(input_grid) > 0:
		counter +=1
		input_grid = sorted(input_grid, key=attrgetter('objective'))
		current_input_grid = input_grid.pop()
		if 0 in current_input_grid.grid:
			#print(current_input_grid)
			cube_constraint, cube_solution = propagateConstraint(current_input_grid.grid)
			input_grid += findNextGrids(cube_constraint, cube_solution, current_input_grid.grid)
		else:
			print(f'Solution found in {counter} iterations')
			break
	return current_input_grid.grid
	

def lambda_handler(event, context):
	for record in event['Records']:
		bucket = record['s3']['bucket']['name']
		key = unquote_plus(record['s3']['object']['key'])
		tmpkey = key.replace('/', '')
		download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
		s3_client.download_file(bucket, key, download_path)
		print(solve_sudoku(download_path))
