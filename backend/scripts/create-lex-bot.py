#!/usr/bin/env python3
"""
Create Amazon Lex V2 bot for photo search natural language processing.
"""

import boto3
import json
import time

REGION = 'us-east-1'
BOT_NAME = 'PhotoSearchBot'
BOT_ALIAS = 'prod'

def delete_existing_bot(lex, bot_id):
    """Delete existing bot."""
    try:
        # Delete aliases first
        aliases = lex.list_bot_aliases(botId=bot_id)
        for alias in aliases.get('botAliasSummaries', []):
            print(f"Deleting alias: {alias['botAliasName']}")
            lex.delete_bot_alias(botAliasId=alias['botAliasId'], botId=bot_id)
            time.sleep(2)
        
        # Delete bot
        print(f"Deleting bot: {bot_id}")
        lex.delete_bot(botId=bot_id, skipResourceInUseCheck=True)
        time.sleep(5)
    except Exception as e:
        print(f"Error deleting bot: {e}")

def create_bot():
    """Create the Lex V2 bot."""
    
    lex = boto3.client('lexv2-models', region_name=REGION)
    
    # Check if bot already exists and delete it
    try:
        response = lex.list_bots()
        for bot in response.get('botSummaries', []):
            if bot['botName'] == BOT_NAME:
                print(f"Bot {BOT_NAME} already exists. Deleting...")
                delete_existing_bot(lex, bot['botId'])
    except Exception as e:
        print(f"Error checking for existing bot: {e}")
    
    # Get IAM role
    iam = boto3.client('iam', region_name=REGION)
    
    role_name = 'LexBotRole'
    try:
        role = iam.get_role(RoleName=role_name)
        role_arn = role['Role']['Arn']
        print(f"Using existing role: {role_arn}")
    except iam.exceptions.NoSuchEntityException:
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lexv2.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        role = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Role for Lex V2 bot'
        )
        role_arn = role['Role']['Arn']
        
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/AmazonLexFullAccess'
        )
        print(f"Created role: {role_arn}")
        time.sleep(10)
    
    # Create bot
    print(f"Creating bot: {BOT_NAME}...")
    
    response = lex.create_bot(
        botName=BOT_NAME,
        description='Photo search bot for natural language queries',
        roleArn=role_arn,
        dataPrivacy={
            'childDirected': False
        },
        idleSessionTTLInSeconds=300
    )
    
    bot_id = response['botId']
    print(f"Created bot with ID: {bot_id}")
    
    time.sleep(5)
    
    # Create locale (English)
    print("Creating English locale...")
    lex.create_bot_locale(
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US',
        nluIntentConfidenceThreshold=0.40
    )
    
    time.sleep(5)
    
    # Create SearchIntent with slots inline
    print("Creating SearchIntent...")
    intent_response = lex.create_intent(
        intentName='SearchIntent',
        description='Intent to search for photos',
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US',
        sampleUtterances=[
            {'utterance': 'show me {keyword1}'},
            {'utterance': 'find {keyword1}'},
            {'utterance': 'search for {keyword1}'},
            {'utterance': 'photos of {keyword1}'},
            {'utterance': 'pictures of {keyword1}'},
            {'utterance': 'show me {keyword1} and {keyword2}'},
            {'utterance': 'find {keyword1} and {keyword2}'},
            {'utterance': 'search for {keyword1} and {keyword2}'},
            {'utterance': 'photos with {keyword1} and {keyword2}'},
            {'utterance': 'show me photos with {keyword1}'},
            {'utterance': 'I want to see {keyword1}'},
            {'utterance': '{keyword1}'},
            {'utterance': '{keyword1} and {keyword2}'},
            {'utterance': 'show {keyword1}'},
            {'utterance': 'get {keyword1}'},
            {'utterance': 'look for {keyword1}'},
            {'utterance': 'show me photos of {keyword1} and {keyword2}'},
        ],
        fulfillmentCodeHook={
            'enabled': False
        }
    )
    
    intent_id = intent_response['intentId']
    print(f"Created intent with ID: {intent_id}")
    
    time.sleep(3)
    
    # Create keyword1 slot with priority
    print("Creating slots...")
    lex.create_slot(
        slotName='keyword1',
        description='First search keyword',
        slotTypeId='AMAZON.AlphaNumeric',
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US',
        intentId=intent_id,
        slotConstraint='Optional',
        valueElicitationSetting={
            'slotConstraint': 'Optional',
            'promptSpecification': {
                'messageGroups': [
                    {
                        'message': {
                            'plainTextMessage': {
                                'value': 'What would you like to search for?'
                            }
                        }
                    }
                ],
                'maxRetries': 2
            },
            'sampleUtterances': []
        }
    )
    
    # Create keyword2 slot
    lex.create_slot(
        slotName='keyword2',
        description='Second search keyword',
        slotTypeId='AMAZON.AlphaNumeric',
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US',
        intentId=intent_id,
        slotConstraint='Optional',
        valueElicitationSetting={
            'slotConstraint': 'Optional',
            'promptSpecification': {
                'messageGroups': [
                    {
                        'message': {
                            'plainTextMessage': {
                                'value': 'Any other keyword?'
                            }
                        }
                    }
                ],
                'maxRetries': 2
            },
            'sampleUtterances': []
        }
    )
    
    print("Created slots: keyword1, keyword2")
    
    time.sleep(3)
    
    # Update intent with slot priorities
    print("Updating intent with slot priorities...")
    
    # Get slot IDs
    slots = lex.list_slots(
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US',
        intentId=intent_id
    )
    
    slot_priorities = []
    for slot in slots.get('slotSummaries', []):
        priority = 1 if slot['slotName'] == 'keyword1' else 2
        slot_priorities.append({
            'priority': priority,
            'slotId': slot['slotId']
        })
    
    lex.update_intent(
        intentId=intent_id,
        intentName='SearchIntent',
        description='Intent to search for photos',
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US',
        sampleUtterances=[
            {'utterance': 'show me {keyword1}'},
            {'utterance': 'find {keyword1}'},
            {'utterance': 'search for {keyword1}'},
            {'utterance': 'photos of {keyword1}'},
            {'utterance': 'pictures of {keyword1}'},
            {'utterance': 'show me {keyword1} and {keyword2}'},
            {'utterance': 'find {keyword1} and {keyword2}'},
            {'utterance': 'search for {keyword1} and {keyword2}'},
            {'utterance': 'photos with {keyword1} and {keyword2}'},
            {'utterance': 'show me photos with {keyword1}'},
            {'utterance': 'I want to see {keyword1}'},
            {'utterance': '{keyword1}'},
            {'utterance': '{keyword1} and {keyword2}'},
            {'utterance': 'show {keyword1}'},
            {'utterance': 'get {keyword1}'},
            {'utterance': 'look for {keyword1}'},
            {'utterance': 'show me photos of {keyword1} and {keyword2}'},
        ],
        slotPriorities=slot_priorities
    )
    
    print("Updated intent with slot priorities")
    
    time.sleep(3)
    
    # Build the bot locale
    print("Building bot locale...")
    lex.build_bot_locale(
        botId=bot_id,
        botVersion='DRAFT',
        localeId='en_US'
    )
    
    # Wait for build
    print("Waiting for build to complete...")
    for i in range(30):
        time.sleep(10)
        response = lex.describe_bot_locale(
            botId=bot_id,
            botVersion='DRAFT',
            localeId='en_US'
        )
        status = response['botLocaleStatus']
        print(f"  Build status: {status}")
        if status == 'Built':
            break
        elif status == 'Failed':
            print(f"  Build failed: {response.get('failureReasons', 'Unknown')}")
            return bot_id, None
    
    # Create bot version
    print("Creating bot version...")
    version_response = lex.create_bot_version(
        botId=bot_id,
        botVersionLocaleSpecification={
            'en_US': {
                'sourceBotVersion': 'DRAFT'
            }
        }
    )
    bot_version = version_response['botVersion']
    print(f"Created version: {bot_version}")
    
    # Wait for version to be available
    print("Waiting for version to be available...")
    for i in range(12):
        time.sleep(5)
        response = lex.describe_bot_version(
            botId=bot_id,
            botVersion=bot_version
        )
        status = response['botStatus']
        print(f"  Version status: {status}")
        if status == 'Available':
            break
    
    # Create bot alias
    print(f"Creating bot alias: {BOT_ALIAS}...")
    alias_response = lex.create_bot_alias(
        botAliasName=BOT_ALIAS,
        botId=bot_id,
        botVersion=bot_version
    )
    bot_alias_id = alias_response['botAliasId']
    print(f"Created alias with ID: {bot_alias_id}")
    
    print("\n" + "="*50)
    print("Lex Bot Created Successfully!")
    print("="*50)
    print(f"Bot ID: {bot_id}")
    print(f"Bot Alias ID: {bot_alias_id}")
    print(f"Bot Version: {bot_version}")
    print("\nUpdate your search Lambda with these values:")
    print(f"  LEX_BOT_ID = {bot_id}")
    print(f"  LEX_BOT_ALIAS_ID = {bot_alias_id}")
    print("="*50)
    
    return bot_id, bot_alias_id

if __name__ == "__main__":
    create_bot()
