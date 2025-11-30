#!/usr/bin/env python3
import boto3
import time

BOT_ID = 'LXTPLV0TAR'
ALIAS_ID = 'JQBUTXF7EV'

lex = boto3.client('lexv2-models', region_name='us-east-1')

print("Updating alias with locale settings...")
try:
    response = lex.update_bot_alias(
        botAliasId=ALIAS_ID,
        botAliasName='prod',
        botId=BOT_ID,
        botVersion='2',
        botAliasLocaleSettings={
            'en_US': {
                'enabled': True
            }
        }
    )
    print("Alias updated with locale settings!")
    print(f"Status: {response.get('botAliasStatus')}")
except Exception as e:
    print(f"Error: {e}")

# Wait for alias to be available
print("Waiting for alias to be available...")
for i in range(6):
    time.sleep(5)
    response = lex.describe_bot_alias(
        botAliasId=ALIAS_ID,
        botId=BOT_ID
    )
    status = response.get('botAliasStatus')
    print(f"  Status: {status}")
    if status == 'Available':
        break

