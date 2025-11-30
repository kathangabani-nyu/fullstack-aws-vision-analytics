#!/usr/bin/env python3
"""
Rebuild and configure the existing Lex bot.
"""

import boto3
import time

BOT_ID = 'LXTPLV0TAR'
REGION = 'us-east-1'

def rebuild_bot():
    lex = boto3.client('lexv2-models', region_name=REGION)
    
    # Check current locale status
    print("Checking bot locale status...")
    response = lex.describe_bot_locale(
        botId=BOT_ID,
        botVersion='DRAFT',
        localeId='en_US'
    )
    status = response['botLocaleStatus']
    print(f"Current status: {status}")
    
    if status == 'Failed':
        print(f"Failure reasons: {response.get('failureReasons', 'Unknown')}")
    
    # Get intent and update slot priorities if needed
    print("\nChecking SearchIntent...")
    intents = lex.list_intents(
        botId=BOT_ID,
        botVersion='DRAFT',
        localeId='en_US'
    )
    
    search_intent_id = None
    for intent in intents.get('intentSummaries', []):
        if intent['intentName'] == 'SearchIntent':
            search_intent_id = intent['intentId']
            break
    
    if search_intent_id:
        print(f"Found SearchIntent: {search_intent_id}")
        
        # Get slots
        slots = lex.list_slots(
            botId=BOT_ID,
            botVersion='DRAFT',
            localeId='en_US',
            intentId=search_intent_id
        )
        
        slot_priorities = []
        for slot in slots.get('slotSummaries', []):
            print(f"  Slot: {slot['slotName']}, ID: {slot['slotId']}")
            priority = 1 if slot['slotName'] == 'keyword1' else 2
            slot_priorities.append({
                'priority': priority,
                'slotId': slot['slotId']
            })
        
        if slot_priorities:
            print("\nUpdating intent with slot priorities...")
            lex.update_intent(
                intentId=search_intent_id,
                intentName='SearchIntent',
                description='Intent to search for photos',
                botId=BOT_ID,
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
                ],
                slotPriorities=slot_priorities
            )
            print("Updated slot priorities")
    
    # Rebuild locale
    print("\nRebuilding bot locale...")
    lex.build_bot_locale(
        botId=BOT_ID,
        botVersion='DRAFT',
        localeId='en_US'
    )
    
    # Wait for build
    print("Waiting for build to complete...")
    for i in range(30):
        time.sleep(10)
        response = lex.describe_bot_locale(
            botId=BOT_ID,
            botVersion='DRAFT',
            localeId='en_US'
        )
        status = response['botLocaleStatus']
        print(f"  Build status: {status}")
        if status == 'Built':
            break
        elif status == 'Failed':
            print(f"  Build failed: {response.get('failureReasons', 'Unknown')}")
            return None, None
    
    # Create new bot version
    print("\nCreating new bot version...")
    version_response = lex.create_bot_version(
        botId=BOT_ID,
        botVersionLocaleSpecification={
            'en_US': {
                'sourceBotVersion': 'DRAFT'
            }
        }
    )
    bot_version = version_response['botVersion']
    print(f"Created version: {bot_version}")
    
    # Wait for version
    print("Waiting for version to be available...")
    for i in range(12):
        time.sleep(5)
        response = lex.describe_bot_version(
            botId=BOT_ID,
            botVersion=bot_version
        )
        status = response['botStatus']
        print(f"  Version status: {status}")
        if status == 'Available':
            break
    
    # Update existing alias or create new one
    print("\nUpdating bot alias...")
    try:
        lex.update_bot_alias(
            botAliasId='TSTALIASID',
            botAliasName='TestBotAlias',
            botId=BOT_ID,
            botVersion=bot_version
        )
        bot_alias_id = 'TSTALIASID'
        print(f"Updated alias to version {bot_version}")
    except Exception as e:
        print(f"Error updating alias: {e}")
        print("Creating new alias...")
        alias_response = lex.create_bot_alias(
            botAliasName='prod',
            botId=BOT_ID,
            botVersion=bot_version
        )
        bot_alias_id = alias_response['botAliasId']
        print(f"Created new alias: {bot_alias_id}")
    
    print("\n" + "="*50)
    print("Lex Bot Rebuilt Successfully!")
    print("="*50)
    print(f"Bot ID: {BOT_ID}")
    print(f"Bot Alias ID: {bot_alias_id}")
    print(f"Bot Version: {bot_version}")
    print("="*50)
    
    return BOT_ID, bot_alias_id

if __name__ == "__main__":
    rebuild_bot()

