#!/usr/bin/env python3
import boto3

BOT_ID = 'LXTPLV0TAR'
ALIAS_ID = 'JQBUTXF7EV'

lex_runtime = boto3.client('lexv2-runtime', region_name='us-east-1')

test_queries = [
    'show me cats',
    'dogs',
    'cats and dogs',
    'show me photos of raccoons',
    'find donkey',
]

for query in test_queries:
    print(f"\nQuery: '{query}'")
    try:
        response = lex_runtime.recognize_text(
            botId=BOT_ID,
            botAliasId=ALIAS_ID,
            localeId='en_US',
            sessionId=f'test-{hash(query)}',
            text=query
        )
        intent = response.get('sessionState', {}).get('intent', {})
        print(f"  Intent: {intent.get('name')}")
        slots = intent.get('slots', {})
        for slot_name, slot_value in slots.items():
            if slot_value:
                value = slot_value.get('value', {}).get('interpretedValue', 'N/A')
                print(f"  {slot_name}: {value}")
    except Exception as e:
        print(f"  Error: {e}")

