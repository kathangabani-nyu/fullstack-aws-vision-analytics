#!/usr/bin/env python3
import boto3
import time

BOT_ID = 'LXTPLV0TAR'
lex = boto3.client('lexv2-models', region_name='us-east-1')

# Delete existing alias
print("Deleting existing alias...")
try:
    lex.delete_bot_alias(
        botAliasId='TSTALIASID',
        botId=BOT_ID,
        skipResourceInUseCheck=True
    )
    print("Deleted!")
    time.sleep(5)
except Exception as e:
    print(f"Error deleting: {e}")

# Create new version from built DRAFT
print("\nCreating new bot version...")
try:
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
except Exception as e:
    print(f"Error creating version: {e}")
    # Use existing version
    versions = lex.list_bot_versions(botId=BOT_ID)
    for v in versions.get('botVersionSummaries', []):
        if v['botVersion'] != 'DRAFT' and v['botStatus'] == 'Available':
            bot_version = v['botVersion']
            print(f"Using existing version: {bot_version}")
            break

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

# Create new alias
print("\nCreating new alias 'prod'...")
try:
    alias_response = lex.create_bot_alias(
        botAliasName='prod',
        botId=BOT_ID,
        botVersion=bot_version
    )
    bot_alias_id = alias_response['botAliasId']
    print(f"Created alias: {bot_alias_id}")
except Exception as e:
    print(f"Error: {e}")
    bot_alias_id = None

if bot_alias_id:
    print("\n" + "="*50)
    print("Success!")
    print(f"Bot ID: {BOT_ID}")
    print(f"Bot Alias ID: {bot_alias_id}")
    print("="*50)

