#!/usr/bin/env python3
import boto3

lex = boto3.client('lexv2-models', region_name='us-east-1')
bots = lex.list_bots()
for bot in bots.get('botSummaries', []):
    print(f"Bot: {bot['botName']}, ID: {bot['botId']}, Status: {bot['botStatus']}")
    if bot['botName'] == 'PhotoSearchBot':
        aliases = lex.list_bot_aliases(botId=bot['botId'])
        for alias in aliases.get('botAliasSummaries', []):
            print(f"  Alias: {alias['botAliasName']}, ID: {alias['botAliasId']}, Status: {alias.get('botAliasStatus', 'N/A')}")

