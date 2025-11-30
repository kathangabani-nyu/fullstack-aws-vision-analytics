#!/usr/bin/env python3
"""
Fix and rebuild the Lex bot by removing empty slot types.
"""

import boto3
import time

BOT_ID = 'LXTPLV0TAR'
REGION = 'us-east-1'

def fix_bot():
    lex = boto3.client('lexv2-models', region_name=REGION)
    
    # Delete the empty PhotoKeyword slot type
    print("Listing slot types...")
    slot_types = lex.list_slot_types(
        botId=BOT_ID,
        botVersion='DRAFT',
        localeId='en_US'
    )
    
    for st in slot_types.get('slotTypeSummaries', []):
        print(f"  Slot type: {st['slotTypeName']}, ID: {st['slotTypeId']}")
        if st['slotTypeName'] == 'PhotoKeyword':
            print(f"  Deleting PhotoKeyword slot type...")
            try:
                lex.delete_slot_type(
                    slotTypeId=st['slotTypeId'],
                    botId=BOT_ID,
                    botVersion='DRAFT',
                    localeId='en_US'
                )
                print("  Deleted!")
            except Exception as e:
                print(f"  Error deleting: {e}")
    
    time.sleep(3)
    
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
    
    # Update existing alias
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
        return BOT_ID, None
    
    print("\n" + "="*50)
    print("Lex Bot Fixed Successfully!")
    print("="*50)
    print(f"Bot ID: {BOT_ID}")
    print(f"Bot Alias ID: {bot_alias_id}")
    print(f"Bot Version: {bot_version}")
    print("="*50)
    
    return BOT_ID, bot_alias_id

if __name__ == "__main__":
    fix_bot()

