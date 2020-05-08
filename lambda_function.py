import boto3
import os
import sys
import uuid
import json 
import numpy as np

from urllib.parse import unquote_plus
from collections import namedtuple
from operator import attrgetter
from trp import Document

s3_client = boto3.client('s3')
txt_client = boto3.client('textract')

global SUDOKU_SIZE
SUDOKU_SIZE = 9


def lambda_handler(event, context):
	# Read inputs
	if 'Records' in event:
		record = event['Records'][0] # only 1 record 
		if 'eventSource' in record:
			if record['eventSource'] == 'aws:sqs':
				grid_id, input_matrix = sqs_handler(record)
			elif record['eventSource'] == 'aws:s3':
				grid_id, input_matrix = s3_handler(record)
			else:
				raise Exception(f"No compatible eventSource found in record: {record['eventSource']}")
		else:
			raise Exception(f'No eventSource found in record {record}')
	else:
		raise Exception(f'No Records found in event {event}')
	print(f'Grid ID: {grid_id} \nInput matrix: \n {input_matrix}')
	# Call solver
	input_matrix_saved = [input_matrix.copy()]
	solution, sol_found = solve_sudoku(grid_list = [input_matrix])
	# try agaon one number at a time in case it fails
	if not sol_found :
		print('Try again filling one number at a time')
		solution, sol_found = solve_sudoku(grid_list = [input_matrix], one_at_a_time = True)
	# Send solution to DynamoDB
	dynamodb_table = boto3.resource('dynamodb').Table('sudokuGridRecords')
	if sol_found:
		print('Solution grid \n', solution)
		send_sol_to_db = dynamodb_table.put_item(
			Item = {
			'grid_id': grid_id, 
			'input': json.dumps(np.array(input_matrix_saved).ravel().tolist()),
			'solution': json.dumps(np.array(solution).ravel().tolist()),
			}
		)
	else:
		print('No solution found')
		send_sol_to_db = dynamodb_table.put_item(
			Item = {
			'grid_id': grid_id, 
			'input': json.dumps(np.array(input_matrix_saved).ravel().tolist()),
			'solution': 'No solution found',
			}
		)
	if send_sol_to_db['ResponseMetadata']['HTTPStatusCode'] == 200:
		print('Solution sent to Dynamodb')
	else:
		print(f'Error in writing solution for grid {grid_id} into DynamoDB')
		raise Exception({send_sol_to_db["ResponseMetadata"]})


def sqs_handler(record):
	print(f'Reading event from {record["eventSource"]}')
	grid_id = json.loads(record['body'])['grid_id']
	input_numbers = json.loads(record['body'])['input_matrix']
	SUDOKU_SIZE = int(np.sqrt(len(input_numbers)))
	input_matrix = np.matrix(np.array(input_numbers).reshape((SUDOKU_SIZE, SUDOKU_SIZE)))
	return grid_id, input_matrix


def s3_handler(record):
	#process using S3 object
	response = txt_client.analyze_document(
		Document=
		{
			'S3Object': 
			{
				'Bucket': record['s3']['bucket']['name'], 
				'Name': record['s3']['object']['key'],
			}
		},
		FeatureTypes=["TABLES"]
	)
	grid_id = os.path.splitext(record['s3']['object']['key'].replace('incoming/',''))[0]
	#Get the text blocks
	doc = Document(response)
	input_matrix = []
	for page in doc.pages:
		# Print tables
		for table in page.tables:
			for r, row in enumerate(table.rows):
				for c, cell in enumerate(row.cells):
					number = cell.text.replace('NOT_SELECTED,','').replace('SELECTED,','').replace(' ','')
					if number == '':
						number = 0
					try:
						input_matrix += [int(number)]
					except:
						input_matrix += [number]
					#print("Table[{}][{}] = {}".format(r, c, ttt))
	if len(input_matrix) == 81 and all([isinstance(i, int) for i in input_matrix]):
		input_matrix = np.matrix(input_matrix).reshape(9,9)
	else:
		dynamodb_table = boto3.resource('dynamodb').Table('sudokuGridRecords')
		print('Grid not recognized')
		send_sol_to_db = dynamodb_table.put_item(
			Item = {
			'grid_id': grid_id, 
			'input': json.dumps(np.array(input_matrix).ravel().tolist()),
			'solution': 'Grid could not be read',
			}
		)
		raise Exception(f'Sudoku not detected in picture {grid_id}')
	return grid_id, input_matrix


def solve_sudoku(grid_list, one_at_a_time=False):
	counter = 0
	solution_found = False
	while len(grid_list) > 0:
		counter +=1
		current_input_grid = grid_list.pop()
		if 0 in current_input_grid:
			cube_constraint, cube_solution = propagateConstraint(current_input_grid)
			if gridIsNotFeasible(cube_solution):
				break
			grid_list += findNextGrids(cube_constraint, cube_solution, current_input_grid, one_at_a_time)
			if counter % 1000 == 0:
				print('Iterations:', counter, '| Queue length:', len(grid_list), '| Left to find:', 81-np.sum(numberIs(0,cube_solution),axis=None))
		else:
			solution_found = True
			print(f'Solution found in {counter} iterations')
			break
	return current_input_grid, solution_found


def gridIsNotFeasible(cube_solution):
	feasibility = []
	for number_grid in cube_solution:
		# column check
		col_feasibility = all(np.sum(number_grid, axis=0) < 2)
		# row check
		row_feasibility = all(np.sum(number_grid, axis=1) < 2)
		# small square constraint
		sqrt_size = int(np.sqrt(SUDOKU_SIZE))
		number_grid_box = [np.sum(number_grid[int(sqrt_size*np.floor(i/sqrt_size)):int(sqrt_size*np.floor(i/sqrt_size)+sqrt_size), int(sqrt_size*i-SUDOKU_SIZE*np.floor(i/sqrt_size)):int(sqrt_size*i-SUDOKU_SIZE*np.floor(i/sqrt_size)+sqrt_size)], axis=None)< 2 for i in range(SUDOKU_SIZE)]
		box_feasibility = all(number_grid_box)
		feasibility += [col_feasibility and row_feasibility and box_feasibility]
	return not all(feasibility)


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
			if 1 in mat[row_s:row_e, col_s:col_e]:
				cube_constraint[idx][row_s:row_e, col_s:col_e] = np.ones((sqrt_size,sqrt_size))
	return cube_constraint, cube_solution


def findNextGrids(cube_constraint, cube_solution, current_input_matrix, one_at_a_time):
	# check which numbers are fully constraint (8) and still unknown
	new_number_posistion = np.logical_and(np.sum(cube_constraint, axis=0)==(SUDOKU_SIZE-1), numberIs(0, cube_solution)==0)
	# if at least one is fully constrained, fill the grid with its value
	if True in new_number_posistion:
		# find the new number values
		new_numbers = np.zeros((SUDOKU_SIZE,SUDOKU_SIZE))
		for idx, mat in enumerate(cube_constraint):
			new_numbers += (idx+1)*(1-mat)
		if one_at_a_time:
			# fill one number at a time, longer but avoid 16x16 empty grid issue where last 2 lines are filled simultaneously
			single_max_index = np.argmax(new_number_posistion)
			single_line_idx = int(single_max_index/SUDOKU_SIZE)
			single_col_idx = single_max_index % SUDOKU_SIZE
			current_input_matrix[single_line_idx,single_col_idx] = new_numbers[single_line_idx,single_col_idx]
		else:
			# fill multiple numbers in one go, but need to make sure those obeys the sudoku rules
			current_input_matrix[new_number_posistion] = new_numbers[new_number_posistion]
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
	return grid_output


def numberIs(i, cube_solution):
	if i > 0:
		# return the matrix where number i is located
		return cube_solution[i-1]
	elif i == 0:
		# return the matrix to say where the unknowed numbers are
		return np.sum(cube_solution, axis=0)
	else:
		return f'Error: Pleased enter a number between 0 and {SUDOKU_SIZE}'

	

# Deprecated, used for direct invocation from API Gateway but browser timed out before the hardest grid were solved
# Solved by using decoupled invocation
#
#	def api_handler(event):
#		print(f'Reading event from API call')
#		grid_id = json.loads(event['body'])['grid_id']
#		input_numbers = json.loads(event['body'])['input_matrix']
#		SUDOKU_SIZE = int(np.sqrt(len(input_numbers)))
#		input_matrix = np.matrix(np.array(input_numbers).reshape((SUDOKU_SIZE, SUDOKU_SIZE)))
#		solution, sol_found = solve_sudoku(grid_list = [input_matrix])
#		return {"headers": {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, "statusCode": 200, "body": json.dumps({"input": json.dumps(np.array(input_matrix_saved).ravel().tolist()), "sol_found": json.dumps(sol_found), "solution": json.dumps(np.array(solution).ravel().tolist())})}



# Deprecated, used for direct invocation of lambda from S3 outgoing bucket (decoded grid)
#
#def s3_handler(record):
#	# Download file from s3 bucket location to local
#	bucket = record['s3']['bucket']['name']
#	key = unquote_plus(record['s3']['object']['key'])
#	print(f'Reading event from {key}')
#	tmpkey = key.replace('/', '')
#	download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
#	s3_client.download_file(bucket, key, download_path)
#	grid_id = tmpkey.replace('outgoing', '').replace('.txt','')
#	# Open file
#	with open(download_path, 'r') as input_data_file:
#		input_data = input_data_file.read()
#	# Read the sudoku grid
#	lines = input_data.split('\n')
#	SUDOKU_SIZE = len(lines)
#	input_matrix = np.matrix([np.array(l.split(), dtype=int) for l in lines])
#	return grid_id, input_matrix



