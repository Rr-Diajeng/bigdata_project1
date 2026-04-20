import re
import argparse
from pathlib import Path

import pandas as pd


def clean_text(text: str) -> str:
    """
    - lowercase
    - strip whitespace at ends
    - remove URLs and non a–z chars: (http\\S+|www\\S+|[^a-z\\s])
    - collapse multiple spaces into one
    """
    if pd.isna(text):
        return ""

    text = str(text).lower().strip()
    #remove URLs
    text = re.sub(r"http\S+|www\S+", " ", text)
    #keep only letters a-z and spaces
    text = re.sub(r"[^a-z\s]", " ", text)
    #collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Minimal preprocessing for Amazon Fine Food Reviews"
    )
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument(
        "--min_words",
        type=int,
        default=3,
        help="Minimum cleaned word count to keep (for dropping short reviews)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    #read CSV
    df = pd.read_csv(input_path)

    #drop columns ["_id", ""]
    df.columns = [str(c).strip() for c in df.columns]
    drop_cols = [c for c in df.columns if c in ["_id", ""] or str(c).startswith("Unnamed")]
    if drop_cols:
        df = df.drop(columns=drop_cols)

    #drop null values
    df = df.dropna(subset=["Text", "Time"])

    #drop duplicate reviews
    df = df.drop_duplicates(subset=["ProductId", "UserId", "Time", "Text"])

    #convert timestamp (unix to datetime)
    df["review_datetime"] = pd.to_datetime(df["Time"], unit="s", errors="coerce")
    df = df.dropna(subset=["review_datetime"])

    #clean the text reviews
    df["cleaned_text"] = df["Text"].apply(clean_text)

    #drop short reviews (after cleaning)
    df["review_word_count"] = df["cleaned_text"].str.split().str.len()
    df = df[df["review_word_count"] >= args.min_words].copy()

    #save output
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    main()