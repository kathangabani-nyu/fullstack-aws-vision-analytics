#!/usr/bin/env python3
import boto3
import time

BOT_ID = 'LXTPLV0TAR'
lex = boto3.client('lexv2-models', region_name='us-east-1')

# List versions
print("Available versions:")
versions = lex.list_bot_versions(botId=BOT_ID)
for v in versions.get('botVersionSummaries', []):
    print(f"  Version: {v['botVersion']}, Status: {v['botStatus']}")

# Wait and try to update
print("\nWaiting 30 seconds for version propagation...")
time.sleep(30)

# Try updating alias with latest version
versions = lex.list_bot_versions(botId=BOT_ID)
available_versions = [v['botVersion'] for v in versions.get('botVersionSummaries', []) 
                      if v['botStatus'] == 'Available' and v['botVersion'] != 'DRAFT']

if available_versions:
    latest = max(available_versions)
    print(f"Updating alias to version: {latest}")
    try:
        lex.update_bot_alias(
            botAliasId='TSTALIASID',
            botAliasName='TestBotAlias',
            botId=BOT_ID,
            botVersion=latest
        )
        print("Alias updated successfully!")
    except Exception as e:
        print(f"Error: {e}")
        # Try with numeric version
        print("Trying with version number...")
        for v in ['1', '2', '3']:
            try:
                lex.update_bot_alias(
                    botAliasId='TSTALIASID',
                    botAliasName='TestBotAlias',
                    botId=BOT_ID,
                    botVersion=v
                )
                print(f"Alias updated to version {v}!")
                break
            except Exception as e2:
                print(f"  Version {v}: {e2}")
else:
    print("No available versions found")

