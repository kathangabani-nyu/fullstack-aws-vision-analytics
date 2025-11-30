#!/usr/bin/env python3
import boto3

BOT_ID = 'LXTPLV0TAR'
ALIAS_ID = 'TSTALIASID'

lex = boto3.client('lexv2-models', region_name='us-east-1')
lex_runtime = boto3.client('lexv2-runtime', region_name='us-east-1')

# Check intents
print("Checking bot intents...")
intents = lex.list_intents(
    botId=BOT_ID,
    botVersion='DRAFT',
    localeId='en_US'
)
for intent in intents.get('intentSummaries', []):
    print(f"  Intent: {intent['intentName']}, ID: {intent['intentId']}")

# Test recognizing text
print("\nTesting bot with 'show me cats'...")
try:
    response = lex_runtime.recognize_text(
        botId=BOT_ID,
        botAliasId=ALIAS_ID,
        localeId='en_US',
        sessionId='test-session',
        text='show me cats'
    )
    print(f"Intent: {response.get('sessionState', {}).get('intent', {}).get('name')}")
    slots = response.get('sessionState', {}).get('intent', {}).get('slots', {})
    print(f"Slots: {slots}")
except Exception as e:
    print(f"Error: {e}")

print("\nTesting bot with 'cats and dogs'...")
try:
    response = lex_runtime.recognize_text(
        botId=BOT_ID,
        botAliasId=ALIAS_ID,
        localeId='en_US',
        sessionId='test-session-2',
        text='cats and dogs'
    )
    print(f"Intent: {response.get('sessionState', {}).get('intent', {}).get('name')}")
    slots = response.get('sessionState', {}).get('intent', {}).get('slots', {})
    print(f"Slots: {slots}")
except Exception as e:
    print(f"Error: {e}")

