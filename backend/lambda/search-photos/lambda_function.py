import json
import boto3
import os
import logging
import urllib.request
import base64

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lex_client = boto3.client('lexv2-runtime')

# OpenSearch configuration
OPENSEARCH_ENDPOINT = os.environ.get('OPENSEARCH_ENDPOINT')
OPENSEARCH_INDEX = os.environ.get('OPENSEARCH_INDEX', 'photos')
LEX_BOT_ID = os.environ.get('LEX_BOT_ID')
LEX_BOT_ALIAS_ID = os.environ.get('LEX_BOT_ALIAS_ID')

# OpenSearch master user credentials
OPENSEARCH_USERNAME = os.environ.get('OPENSEARCH_USERNAME', 'admin')
OPENSEARCH_PASSWORD = os.environ.get('OPENSEARCH_PASSWORD')


def normalize_keyword(keyword):
    """
    Normalize keyword by removing common suffixes (basic stemming).
    """
    keyword = keyword.lower().strip()
    # Remove common plural/verb suffixes
    if keyword.endswith('ies'):
        return keyword[:-3] + 'y'  # e.g., puppies -> puppy
    if keyword.endswith('es') and len(keyword) > 3:
        return keyword[:-2]  # e.g., boxes -> box
    if keyword.endswith('s') and len(keyword) > 2:
        return keyword[:-1]  # e.g., cats -> cat
    if keyword.endswith('ing') and len(keyword) > 4:
        return keyword[:-3]  # e.g., running -> runn
    return keyword


def extract_keywords_from_lex(query):
    """
    Use Lex bot to extract keywords from natural language query.
    Returns list of keywords or empty list if no keywords found.
    """
    try:
        if not LEX_BOT_ID or not LEX_BOT_ALIAS_ID:
            logger.warning("Lex bot not configured, using query as-is")
            return [query.strip().lower()]
        
        response = lex_client.recognize_text(
            botId=LEX_BOT_ID,
            botAliasId=LEX_BOT_ALIAS_ID,
            localeId='en_US',
            sessionId='search-session',
            text=query
        )
        
        logger.info(f"Lex response: {json.dumps(response)}")
        
        # Extract keywords from Lex response
        keywords = []
        
        # Check if there are slots with values
        if 'interpretations' and len(response.get('interpretations', [])) > 0:
            interpretation = response['interpretations'][0]
            if 'intent' in interpretation and 'slots' in interpretation['intent']:
                slots = interpretation['intent']['slots']
                if slots:
                    for slot_name, slot_value in slots.items():
                        if slot_value and 'value' in slot_value:
                            keyword = slot_value['value']['originalValue']
                            keywords.append(keyword.lower())
        
        # If no keywords found in slots, try to extract from query
        if not keywords:
            # Simple fallback: split query into words
            keywords = [word.lower() for word in query.split() if len(word) > 2]
        
        # Normalize keywords for better matching
        normalized = [normalize_keyword(k) for k in keywords]
        logger.info(f"Extracted keywords: {keywords}, normalized: {normalized}")
        return normalized
        
    except Exception as e:
        logger.error(f"Error extracting keywords from Lex: {str(e)}")
        # Fallback: use query as keyword
        return [normalize_keyword(query.strip().lower())]


def search_opensearch(keywords):
    """
    Search OpenSearch index for photos matching the keywords.
    Returns list of matching photo documents.
    """
    try:
        if not keywords:
            return []
        
        # Build OpenSearch query
        # Search for any of the keywords in the labels array
        # Use wildcard for better matching
        should_clauses = []
        for keyword in keywords:
            # Normalize keyword (basic stemming)
            normalized = normalize_keyword(keyword)
            
            # Add both exact match and prefix match
            should_clauses.append({
                "match": {
                    "labels": normalized
                }
            })
            # Also try wildcard for partial matches
            should_clauses.append({
                "wildcard": {
                    "labels": f"{normalized}*"
                }
            })
        
        query = {
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }
        }
        
        opensearch_url = f"https://{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_search"
        
        # Use urllib with basic auth
        auth = base64.b64encode(f"{OPENSEARCH_USERNAME}:{OPENSEARCH_PASSWORD}".encode('utf-8')).decode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth}"
        }
        
        req = urllib.request.Request(
            opensearch_url,
            data=json.dumps(query).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode('utf-8')
            if response.status != 200:
                logger.error(f"OpenSearch query failed. Status: {response.status}, Response: {response_body}")
                return []
            results = json.loads(response_body)
        
        # Extract photo documents from results
        photos = []
        if 'hits' in results and 'hits' in results['hits']:
            for hit in results['hits']['hits']:
                if '_source' in hit:
                    photos.append(hit['_source'])
        
        logger.info(f"Found {len(photos)} matching photos")
        return photos
        
    except Exception as e:
        logger.error(f"Error searching OpenSearch: {str(e)}")
        return []


def lambda_handler(event, context):
    """
    Lambda function to search photos using natural language queries.
    Receives query from API Gateway and returns matching photos.
    """
    try:
        # Handle OPTIONS preflight request for CORS
        http_method = event.get('httpMethod', '')
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,x-amz-meta-customlabels',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                },
                'body': ''
            }
        
        # Extract query parameter
        query_params = event.get('queryStringParameters') or {}
        query = query_params.get('q', '')
        
        if not query:
            logger.warning("No query parameter provided")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps([])
            }
        
        logger.info(f"Search query: {query}")
        
        # Extract keywords using Lex
        keywords = extract_keywords_from_lex(query)
        
        if not keywords:
            logger.info("No keywords extracted, returning empty results")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps([])
            }
        
        # Search OpenSearch
        results = search_opensearch(keywords)
        
        # Return results
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(results)
        }
        
    except Exception as e:
        logger.error(f"Error processing search request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }

