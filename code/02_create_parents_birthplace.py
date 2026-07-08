import pandas as pd
import numpy as np

# Load data
df = pd.read_csv("../data/EIM23.csv")

# Create parents_birthplace from T12_1 through T12_4
# Structured like T10: 1 = Estonia, 2 = Russia, 3 = Elsewhere
# Priority when multiple selected: Estonia > Russia > Elsewhere
# Don't know only → NaN

def assign_parents_birthplace(row):
    if row["T12_1"] == 1:
        return 1  # Estonia
    elif row["T12_2"] == 1:
        return 2  # Russia
    elif row["T12_3"] == 1:
        return 3  # Elsewhere
    elif row["T12_4"] == 1:
        return np.nan  # Don't know
    else:
        return np.nan

df["parents_birthplace"] = df.apply(assign_parents_birthplace, axis=1)

# Verify
print("parents_birthplace value counts:")
print(df["parents_birthplace"].value_counts(dropna=False).sort_index())

print("\nCross-tab with T10 (respondent's own birthplace):")
print(pd.crosstab(df["T10"], df["parents_birthplace"],
                  rownames=["T10 (self)"], colnames=["parents_birthplace"],
                  margins=True))

# Save
df.to_csv("../data/EIM23.csv", index=False)
print("\nSaved updated dataset with 'parents_birthplace' column.")
