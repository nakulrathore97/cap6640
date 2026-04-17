from urllib.request import urlretrieve
import pandas as pd

# Download parquet containing prompts + hyperparameters (2M subset)
table_url = "https://huggingface.co/datasets/poloclub/diffusiondb/resolve/main/metadata.parquet"
urlretrieve(table_url, "metadata.parquet")

# Load and extract prompts
df = pd.read_parquet("metadata.parquet")
prompts = df["prompt"].dropna().unique()  # unique prompts

# Save to a text file, one prompt per line
with open("diffusiondb_prompts.txt", "w", encoding="utf-8") as f:
    for p in prompts:
        f.write(p.replace("\n", " ") + "\n")

