import json
import os

# Step 1: Load your Google Cloud JSON key file
json_key_path = "chatbot-467212-076f56c6938b.json"  # change if needed

with open(json_key_path, "r") as f:
    data = json.load(f)

# Step 2: Format values for .env
lines = []

for key, value in data.items():
    key_env = f"GCP_{key.upper()}"
    if key == "private_key":
        # Escape newlines properly for .env
        value = value.replace("\n", "\\n")
        value = f"\"{value}\""  # wrap in quotes
    lines.append(f"{key_env}={value}")

# Step 3: Write to .env file
with open(".env", "w") as f:
    f.write("\n".join(lines))

print("[✅] .env file created successfully!")
