import os
from app import app, db

# Delete the existing database file
db_path = 'inventory.db'
if os.path.exists(db_path):
    os.remove(db_path)
    print("Existing database deleted")

# The app.py will automatically recreate everything when imported
print("Database will be recreated when you run the app")
print("\nDefault credentials:")
