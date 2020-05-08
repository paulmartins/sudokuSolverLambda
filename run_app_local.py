import json
from lambda_function import lambda_handler

if __name__ == "__main__":

	# S3 event
	event = {
		"Records": [
			{
				"eventName": "ObjectCreated:",
				"s3":{
					"bucket":{
						"name": "sudoku-app"
					},
					"object":{
						"key": "incoming/e0688ed0-e178-f0c9-7d3a-e167663facc9.png"
					}
				}
			}
		]
	}

	# SQS event
	event = {
		'Records': [
			{
				'messageId': 'f7043941-4222-488b-abc3-0c6ba12fec30', 
				'receiptHandle': 'AQEBIe1q41BPMgWnUIeysM1rO/lW/F//UuY5Yv8QPts6q/wBkJqiS65StStmZfGQHOJDk1gjPcrVSBJj1rJp/4P/AlfYQJJ4sGFzZNpWAV7S2zlx2JMROcOCqod7f1qqXrfwWs24qyFsM0onEm9wLQsZks8YO9v6clyeXBZpv2ucj//El6yjB2NCHwk1vl4NLH+ABJ/TFDDP/m8L7eBt2JXr/1Ks3Ad3YnVcRfYQI5eVR5CQC7CKplrhEMqk1yfprqtJXQVwrOb4gyG9Pd1FToQIjIkUXUzrFfvMoSvO3xbMHgg7f54Ok8iWFxYaa3yYk3pCRvMEJvNPtVdFHkGlAseU7SEpdI47wU2vUPsZaoyYVp2AsRD5ImrvdITrzt+U2wfFZxejpomEXDpp0jajrJQdbA==', 
				'body': '{"grid_id":"c6979947-cc86-031e-4505-a848a39c4b90","input_matrix":[1,2,3,4,5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}', 
				'attributes': 
					{
						'ApproximateReceiveCount': '4', 
						'AWSTraceHeader': 'Root=1-5eb17a0f-20b6c8fe7a4166be4b5a035e', 
						'SentTimestamp': '1588689423109', 
						'SenderId': 'AROA3LFPI57RFYVSEDXJW:BackplaneAssumeRoleSession', 
						'ApproximateFirstReceiveTimestamp': '1588689423109'
					}, 
				'messageAttributes': {}, 
				'md5OfBody': 'c5343c743a5a77dba30b40d6a52e70f4', 
				'eventSource': 'aws:sqs', 
				'eventSourceARN': 'arn:aws:sqs:eu-west-2:779904151522:sudoku-grid-requested', 
				'awsRegion': 'eu-west-2'
			}
		]	
	}
	
	# API event - deprecated
	# event = {'body': '{"input_matrix":[0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0], "grid_id":"aaaa1111222233334444"}'}

	print(json.dumps(event, indent=4))
    lambda_handler(event, {})
    