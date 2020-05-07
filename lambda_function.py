import boto3
import os
import sys
import uuid
import json 
import numpy as np

from urllib.parse import unquote_plus
from collections import namedtuple
from operator import attrgetter

s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')

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
		# fill one number at a time, longer but avoid 16x16 empty grid issue where last 2 lines are filled simultaneously
		#single_max_index = np.argmax(new_number_posistion)
		#single_line_idx = int(single_max_index/SUDOKU_SIZE)
		#single_col_idx = single_max_index % SUDOKU_SIZE
		#current_input_matrix[single_line_idx,single_col_idx] = new_numbers[single_line_idx,single_col_idx]
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


def solve_sudoku(grid_list):
	counter = 0
	solution_found = False
	while len(grid_list) > 0:
		counter +=1
		current_input_grid = grid_list.pop()
		if 0 in current_input_grid:
			cube_constraint, cube_solution = propagateConstraint(current_input_grid)
			grid_list += findNextGrids(cube_constraint, cube_solution, current_input_grid)
			if counter % 1000 == 0:
				print('Iterations:', counter, '| Queue length:', len(grid_list), '| Left to find:', 81-np.sum(numberIs(0,cube_solution),axis=None))
		else:
			solution_found = True
			print(f'Solution found in {counter} iterations')
			break
	return current_input_grid, solution_found


def sqs_handler(record):
	print(f'Reading event from {record["eventSource"]}')
	grid_id = json.loads(record['body'])['grid_id']
	input_numbers = json.loads(record['body'])['input_matrix']
	SUDOKU_SIZE = int(np.sqrt(len(input_numbers)))
	input_matrix = np.matrix(np.array(input_numbers).reshape((SUDOKU_SIZE, SUDOKU_SIZE)))
	return grid_id, input_matrix


def s3_handler(record):
	# Download file from s3 bucket location to local
	bucket = record['s3']['bucket']['name']
	key = unquote_plus(record['s3']['object']['key'])
	print(f'Reading event from {key}')
	tmpkey = key.replace('/', '')
	download_path = '/tmp/{}{}'.format(uuid.uuid4(), tmpkey)
	s3_client.download_file(bucket, key, download_path)
	grid_id = tmpkey.replace('outgoing', '').replace('.txt','')
	# Open file
	with open(download_path, 'r') as input_data_file:
		input_data = input_data_file.read()
	# Read the sudoku grid
	lines = input_data.split('\n')
	SUDOKU_SIZE = len(lines)
	input_matrix = np.matrix([np.array(l.split(), dtype=int) for l in lines])
	return grid_id, input_matrix


def lambda_handler(event, context):
	print('Event received \n', event)
	# AWS resources ID
	all_queue_urls = sqs_client.list_queues()['QueueUrls']
	dl_queue_url = [url for url in all_queue_urls if 'sudoku-grid-requested-dead-letter' in url][0]
	dynamodb_table = boto3.resource('dynamodb').Table('sudokuGridRecords')
	# Read inputs
	if 'Records' in event:
		for record in event['Records']:
			if 'eventSource' in record:
				grid_id, input_matrix = sqs_handler(record)
			elif 'eventName' in record:
				grid_id, input_matrix = s3_handler(record)
		print(f'Grid ID: {grid_id}')
		print(input_matrix)	
		# Call solver
		input_matrix_saved = [input_matrix.copy()]
		solution, sol_found = solve_sudoku(grid_list = [input_matrix])
		# Send solution to DynamoDB
		if sol_found:
			print('Solution grid \n', solution)
			send_sol_to_db = dynamodb_table.put_item(
				Item = {
				'grid_id': grid_id, 
				'input': json.dumps(np.array(input_matrix_saved).ravel().tolist()),
				'solution': json.dumps(np.array(solution).ravel().tolist()),
				}
			)
			if send_sol_to_db['ResponseMetadata']['HTTPStatusCode'] == 200:
				print('Solution sent to Dynamodb')
			else:
				response = sqs.send_message(
					QueueUrl=dl_queue_url,
					DelaySeconds=5,
					MessageAttributes={
					'Title': {
						'DataType': 'String',
						'StringValue': 'Dynamo DB writing error'
						},
					'Author': {
						'DataType': 'String',
						'StringValue': 'AWS Lambda sudokuSolver'
						},
					},
					MessageBody=(f'Error in writing solution found for grid {grid_id} into DynamoDB',
						f'Response: {send_sol_to_db["ResponseMetadata"]}')
					)
				print(response['MessageId'])
		else:
			print('No solution found')
			dynamodb_table = boto3.resource('dynamodb').Table('sudokuGridRecords')
			send_sol_to_db = dynamodb_table.put_item(
				Item = {
				'grid_id': grid_id, 
				'input': json.dumps(np.array(input_matrix_saved).ravel().tolist()),
				'solution': 'No solution found',
				}
			)
		print('Event processed')
	else:
		print('Cannot process event')

	

# Deprecated, used for direct invocation from API Gateway but browser timed out before the hardest grid were solved
#
#	def api_handler(event):
#		print(f'Reading event from API call')
#		grid_id = json.loads(event['body'])['grid_id']
#		input_numbers = json.loads(event['body'])['input_matrix']
#		SUDOKU_SIZE = int(np.sqrt(len(input_numbers)))
#		input_matrix = np.matrix(np.array(input_numbers).reshape((SUDOKU_SIZE, SUDOKU_SIZE)))
#		solution, sol_found = solve_sudoku(grid_list = [input_matrix])
#		return {"headers": {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, "statusCode": 200, "body": json.dumps({"input": json.dumps(np.array(input_matrix_saved).ravel().tolist()), "sol_found": json.dumps(sol_found), "solution": json.dumps(np.array(solution).ravel().tolist())})}

