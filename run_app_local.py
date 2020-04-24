import json
from sudokuSolver_lambda import lambda_function

if __name__ == '__main__':

	event = {
		"Records": [
			{
				"s3":{
					"bucket":{
						"name": "sudoku-app"
					},
					"object":{
						"key": "outgoing/sudoku_01.txt"
					}
				}
			}
		]
	}

	print(json.dumps(event, indent=4))
    lambda_function.lambda_handler(event, {})
    