import json
import boto3
import urllib3

def lambda_handler(event, context):
    try:
        # Parse the request
        body = json.loads(event['body'])
        summoner_name = body.get('summonerName', '').strip()
        tagLine = body.get('tagLine', 'NA1').strip()
        region = body.get('region', 'na1')  # Default to NA1
        regDict = {"na1":"americas", "la1":"americas", "la2":"americas", "br1":"americas", "euw1":"europe", "eun1":"europe", "tr1":"europe", "kr":"asia", "oc1":"asia", "ru":"asia", "jp1":"asia"};
        regionGen = regDict[region]
        
        # Validate input
        if not summoner_name:
            return {
                'statusCode': 400,
              
                'body': json.dumps({'error': 'Summoner name is required'})
            }
        
        # Get API key from Parameter Store
        ssm = boto3.client('ssm')
        parameter = ssm.get_parameter(
            Name='/rift-rewind/riot-api-key',
            WithDecryption=True
        )
        api_key = parameter['Parameter']['Value']
        
        # Initialize HTTP client
        http = urllib3.PoolManager()
        
        # Get summoner data
        summoner_url = f"https://{regionGen}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{summoner_name}/{tagLine}"
                                                        
        headers = {'X-Riot-Token': api_key}
        
        summoner_response = http.request('GET', summoner_url, headers=headers)
        
        if summoner_response.status == 404:
            return {
                'statusCode': 404,
                
                'body': json.dumps({'error': 'Summoner not found'})
            }
        elif summoner_response.status != 200:
            return {
                'statusCode': summoner_response.status,
               
                'body': json.dumps({'error': 'Failed to fetch summoner data'})
            }
        
        summoner_data = json.loads(summoner_response.data.decode('utf-8'))
        
        # Get champion mastery data
        mastery_url = f"https://{region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{summoner_data['puuid']}"
        mastery_response = http.request('GET', mastery_url, headers=headers)
        
        mastery_data = []
        if mastery_response.status == 200:
            mastery_data = json.loads(mastery_response.data.decode('utf-8'))
        elif mastery_response.status != 200:
            return {
                'statusCode': mastery_response.status,
               
                'body': json.dumps({'error': 'Read er num'})
            }
        
        # Format response
        response_data = {
            'summoner': {
                'name': summoner_data['gameName'],
                'puuid': summoner_data['puuid']
            },
            'topChampions': mastery_data[:3]  # Top 3 champions
        }
        
        return {
            'statusCode': 200,
           
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
           
            'body': json.dumps({'error': 'Internal server error'})
        }
