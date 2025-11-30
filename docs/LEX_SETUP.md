# Amazon Lex Bot Setup Guide

This guide provides detailed instructions for creating the Lex bot for photo search.

## Step 1: Create the Bot

1. Navigate to Amazon Lex Console: https://console.aws.amazon.com/lex/
2. Click "Create" → "Custom bot"
3. Fill in the bot configuration:
   - **Bot name**: `PhotoSearchBot`
   - **Language**: English (US)
   - **Output voice**: None (text only)
   - **Session timeout**: 5 minutes
   - **Sentiment analysis**: No
   - **COPPA**: No (unless required)
4. Click "Create"

## Step 2: Create SearchIntent

1. In the bot editor, click "Add intent" → "Create new intent"
2. **Intent name**: `SearchIntent`
3. Click "Save intent"

## Step 3: Add Sample Utterances

Add the following sample utterances to help Lex understand search queries:

### Single Keyword Searches
- `trees`
- `birds`
- `cats`
- `dogs`
- `people`
- `cars`
- `buildings`
- `nature`
- `animals`
- `flowers`

### Natural Language Queries
- `show me trees`
- `show me photos with trees`
- `show me trees and birds`
- `find cats and dogs`
- `photos with trees`
- `pictures of dogs`
- `show me photos with cats`
- `find photos with birds`
- `show me trees and flowers`
- `photos with people and cars`

### Multi-Keyword Searches
- `trees and birds`
- `cats and dogs`
- `people and buildings`
- `nature and animals`
- `flowers and trees`

**Note**: Add at least 10-15 utterances for better training.

## Step 4: Configure Slots (Optional)

For more structured keyword extraction, you can create slots:

1. In the intent editor, go to "Slots" section
2. Click "Add slot"
3. Create a slot:
   - **Slot name**: `Keyword1`
   - **Slot type**: AMAZON.SearchQuery (or create custom type)
   - **Prompt**: "What would you like to search for?"
   - **Required**: No

4. Add another slot:
   - **Slot name**: `Keyword2`
   - **Slot type**: AMAZON.SearchQuery
   - **Prompt**: "Any other keywords?"
   - **Required**: No

**Note**: The Lambda function will handle flexible keyword extraction even without slots, so this is optional.

## Step 5: Build the Bot

1. Click "Build" button (top right)
2. Wait for the build to complete (takes 1-2 minutes)
3. You'll see a success message when build is complete

## Step 6: Test the Bot

1. Use the test window on the right side
2. Try various queries:
   - "trees"
   - "show me trees"
   - "cats and dogs"
3. Verify the bot recognizes the intent correctly

## Step 7: Publish the Bot

1. Click "Publish" button
2. Select "Create new alias"
3. **Alias name**: `PROD`
4. **Description**: Production alias for photo search
5. Click "Publish"

## Step 8: Get Bot IDs

1. Go to bot settings (gear icon)
2. Note the following:
   - **Bot ID**: Found in the bot details (e.g., `XXXXXXXXXX`)
   - **Bot Alias ID**: Go to "Aliases" tab, click on `PROD`, note the Alias ID

These IDs are needed for the Lambda function environment variables.

## Step 9: Update Lambda Environment Variables

After getting the Bot ID and Alias ID, update the search-photos Lambda:

```bash
aws lambda update-function-configuration \
  --function-name search-photos \
  --environment Variables="{OPENSEARCH_ENDPOINT=YOUR_ENDPOINT,OPENSEARCH_INDEX=photos,LEX_BOT_ID=YOUR_BOT_ID,LEX_BOT_ALIAS_ID=YOUR_ALIAS_ID,AWS_REGION=us-east-1}" \
  --region us-east-1
```

Or update via AWS Console:
1. Go to Lambda console
2. Select `search-photos` function
3. Go to Configuration → Environment variables
4. Add/update:
   - `LEX_BOT_ID`: Your bot ID
   - `LEX_BOT_ALIAS_ID`: Your alias ID

## Testing

After setup, test the bot integration:

1. Upload a photo via the frontend
2. Wait for indexing to complete
3. Search using natural language queries
4. Check CloudWatch logs for Lex responses
5. Verify keywords are extracted correctly

## Troubleshooting

### Bot not recognizing queries
- Add more sample utterances
- Rebuild the bot
- Check that the bot is published

### Lambda can't access Lex
- Verify IAM permissions for Lambda to call Lex
- Check that bot ID and alias ID are correct
- Ensure bot is published to the PROD alias

### Keywords not extracted
- Check CloudWatch logs for Lex responses
- Verify slot configuration (if using slots)
- The Lambda has fallback logic to extract keywords from query text

