import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("../data/EIM23.csv")

# Create edu_language from T19_1 through T19_5
# T19_1 = Estonian, T19_2 = Russian, T19_3 = Estonian and Russian,
# T19_4 = Estonian and other, T19_5 = Other language
# Priority: Estonian > Russian > Estonian+Russian > Estonian+other > Other

def assign_edu_language(row):
    if row["T19_1"] == 1:
        return 1  # Estonian
    elif row["T19_2"] == 1:
        return 2  # Russian
    elif row["T19_3"] == 1:
        return 3  # Estonian and Russian
    elif row["T19_4"] == 1:
        return 4  # Estonian and other
    elif row["T19_5"] == 1:
        return 5  # Other language
    else:
        return np.nan

df["edu_language"] = df.apply(assign_edu_language, axis=1)

# Verify
print("edu_language value counts:")
print(df["edu_language"].value_counts(dropna=False).sort_index())
print("\nLabels: 1=Estonian, 2=Russian, 3=Estonian+Russian, 4=Estonian+other, 5=Other")

# Save
df.to_csv("../data/EIM23.csv", index=False)
print("\nSaved updated dataset with 'edu_language' column.")
