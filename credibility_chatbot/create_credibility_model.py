"""
Create a simple ML model for credibility scoring and save it as credibility_model.pkl.
This is a demonstration model for your hybrid credibility system.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import pickle

# -----------------------------
# Step 1: Generate sample dataset
# -----------------------------
# We simulate features that the credibility model might use:
# - content_length: length of the page text
# - domain_length: length of the domain name
# The target is a credibility score between 0.3 and 0.9 (for demonstration).
np.random.seed(42)
num_samples = 100

data = pd.DataFrame({
    "content_length": np.random.randint(500, 10000, num_samples),
    "domain_length": np.random.randint(3, 15, num_samples),
    "credibility_score": np.random.uniform(0.3, 0.9, num_samples)
})

X = data[["content_length", "domain_length"]]
y = data["credibility_score"]

# -----------------------------
# Step 2: Train a simple regression model
# -----------------------------
# Using RandomForestRegressor for simplicity. Any regressor would work for demonstration.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=50, random_state=42)
model.fit(X_train, y_train)

# Optional: print train/test scores
print("Train R^2:", model.score(X_train, y_train))
print("Test R^2:", model.score(X_test, y_test))

# -----------------------------
# Step 3: Save the model to a pickle file
# -----------------------------
with open("credibility_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("credibility_model.pkl created successfully! Place it in the same folder as assess_credibility.py")
