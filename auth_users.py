# This script will add the user IDs to your MongoDB authorized_users collection in bulk.
# Not required for the bot.

from pymongo import MongoClient
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# MongoDB configuration
MONGODB_URI = os.environ["MONGODB_URI"]
client = MongoClient(MONGODB_URI)
db = client['pixeldrain_bot']
authorized_users_col = db['authorized_users']

# List of user IDs to be added (replace with actual IDs)
user_ids = [
    123456789, 123456789 
]

# Insert user IDs into the authorized_users collection
for user_id in user_ids:
    if not authorized_users_col.find_one({"user_id": user_id}):
        authorized_users_col.insert_one({"user_id": user_id})
        print(f"User {user_id} has been added to the authorized users.")
    else:
        print(f"User {user_id} is already in the authorized users.")

print("User ID insertion completed.")
