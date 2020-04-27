import json
from lambda_function import lambda_handler

if __name__ == "__main__":

	event = {
		"Records": [
			{
				"eventName": "ObjectCreated:",
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

	event = {'resource': '/solver', 'path': '/solver', 'httpMethod': 'POST', 'headers': {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8', 'CloudFront-Forwarded-Proto': 'https', 'CloudFront-Is-Desktop-Viewer': 'true', 'CloudFront-Is-Mobile-Viewer': 'false', 'CloudFront-Is-SmartTV-Viewer': 'false', 'CloudFront-Is-Tablet-Viewer': 'false', 'CloudFront-Viewer-Country': 'GB', 'content-type': 'application/json', 'dnt': '1', 'Host': 'd1zj2gzfll.execute-api.eu-west-2.amazonaws.com', 'origin': 'null', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'cross-site', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36', 'Via': '2.0 10614187afbc9547b57f699efd196655.cloudfront.net (CloudFront)', 'X-Amz-Cf-Id': 'dx8ThZ4CJ0_7x9c8VTWr1Fa7xf_6iD-zwPE5b0OSKUJqiRVHPV0dgg==', 'X-Amzn-Trace-Id': 'Root=1-5ea37a9a-40c431011a1e243de2ec7c3e', 'x-api-key': 'GNwuLiYerN9qHCEH5MbLA5W2Jlp3yBkYGn8xVhC8', 'X-Forwarded-For': '80.43.65.108, 70.132.46.70', 'X-Forwarded-Port': '443', 'X-Forwarded-Proto': 'https'}, 'multiValueHeaders': {'Accept': ['*/*'], 'Accept-Encoding': ['gzip, deflate, br'], 'Accept-Language': ['en-GB,en-US;q=0.9,en;q=0.8'], 'CloudFront-Forwarded-Proto': ['https'], 'CloudFront-Is-Desktop-Viewer': ['true'], 'CloudFront-Is-Mobile-Viewer': ['false'], 'CloudFront-Is-SmartTV-Viewer': ['false'], 'CloudFront-Is-Tablet-Viewer': ['false'], 'CloudFront-Viewer-Country': ['GB'], 'content-type': ['application/json'], 'dnt': ['1'], 'Host': ['d1zj2gzfll.execute-api.eu-west-2.amazonaws.com'], 'origin': ['null'], 'sec-fetch-mode': ['cors'], 'sec-fetch-site': ['cross-site'], 'User-Agent': ['Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'], 'Via': ['2.0 10614187afbc9547b57f699efd196655.cloudfront.net (CloudFront)'], 'X-Amz-Cf-Id': ['dx8ThZ4CJ0_7x9c8VTWr1Fa7xf_6iD-zwPE5b0OSKUJqiRVHPV0dgg=='], 'X-Amzn-Trace-Id': ['Root=1-5ea37a9a-40c431011a1e243de2ec7c3e'], 'x-api-key': ['GNwuLiYerN9qHCEH5MbLA5W2Jlp3yBkYGn8xVhC8'], 'X-Forwarded-For': ['80.43.65.108, 70.132.46.70'], 'X-Forwarded-Port': ['443'], 'X-Forwarded-Proto': ['https']}, 'requestContext': {'resourceId': '965ii0', 'resourcePath': '/solver', 'httpMethod': 'POST', 'extendedRequestId': 'LhAYJExorPEFnLw=', 'requestTime': '24/Apr/2020:23:47:38 +0000', 'path': '/prod/solver', 'accountId': '779904151522', 'protocol': 'HTTP/1.1', 'stage': 'prod', 'domainPrefix': 'd1zj2gzfll', 'requestTimeEpoch': 1587772058462, 'requestId': 'be2e56c1-14f5-4a14-b375-87be511cece1', 'identity': {'apiKey': 'GNwuLiYerN9qHCEH5MbLA5W2Jlp3yBkYGn8xVhC8', 'apiKeyId': '035rkuvn6d', 'userAgent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36', 'sourceIp': '80.43.65.108'}, 'domainName': 'd1zj2gzfll.execute-api.eu-west-2.amazonaws.com', 'apiId': 'd1zj2gzfll'}, 'body': {'input_matrix': [0,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}, 'isBase64Encoded': 'False'}
	event = {'body': '{"input_matrix":[0,0,0,7,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]}'}

	print(json.dumps(event, indent=4))
    lambda_handler(event, {})
    