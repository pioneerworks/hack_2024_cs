import pandas as pd
import ast
import re

def clean_slack_data(raw_message):
    try:
        # Convert string representation of list to actual list
        messages = ast.literal_eval(raw_message)
        
        cleaned_messages = []
        for message in messages:
            # Skip empty messages
            if not message.strip():
                continue
                
            # Skip system messages about file uploads
            if "uploaded" in message and "file(s)" in message:
                continue
                
            # Skip issue creation/closure messages
            if message.startswith("Issue created:") or message == "This request was closed.":
                continue
            
            # Replace all user mentions (pattern: <@U...>) with @user
            message = re.sub(r'<@U[A-Z0-9]+>', '@user', message)
            
            # Remove URLs
            message = re.sub(r'<https?://[^>]+>', '', message)
            
            # Remove HTML entities
            message = message.replace("&amp;", "&")
            
            # Remove redundant newlines and clean up spacing
            message = ' '.join(message.split())
            
            if message.strip():  # Only add non-empty messages
                cleaned_messages.append(message)
        
        # Join the cleaned messages with a separator
        return ' | '.join(cleaned_messages)
    except Exception as e:
        print(f"Error processing message: {e}")
        return raw_message  # Return original if processing fails

# Read the CSV file
df = pd.read_csv('data_sources/slack_channel_data/#advanced-support_large_replies.csv')

# Clean the specific column (replace 'conversation_column' with your column name)
df['content'] = df['conversation'].apply(clean_slack_data)
df['title'] = ''
df = df[['url', 'title', 'content']]

# Save the cleaned data to a new CSV
df.to_csv('data_sources/processed_data_compiled/processed_slack_data.csv', index=False)
