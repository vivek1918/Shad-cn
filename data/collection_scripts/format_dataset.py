import json
from pathlib import Path

def format_dataset():
    try:
        # Create processed directory if it doesn't exist
        processed_dir = Path("data/processed/")
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Load raw data from different sources with error handling
        raw_files = {
            "magicui": "data/raw/magicui.json",
            "aceternity": "data/raw/aceternity.json"
        }

        combined_data = []
        for name, file_path in raw_files.items():
            try:
                path = Path(file_path)
                if not path.exists():
                    raise FileNotFoundError(f"Raw data file not found: {file_path}")
                
                data = json.loads(path.read_text(encoding="utf-8"))
                combined_data.extend(data)
                print(f"Successfully loaded {len(data)} items from {name}")
            except Exception as e:
                print(f"Error loading {name} data: {str(e)}")
                raise

        # Format for fine-tuning
        formatted = []
        for item in combined_data:
            try:
                formatted.append({
                    "text": f"<|prompt|>{item['prompt']}<|completion|>{item['completion']}<|endoftext|>"
                })
            except KeyError as e:
                print(f"Missing required field in item: {str(e)}")
                continue  # Skip malformed items

        # Save the formatted dataset
        output_path = processed_dir / "dataset.jsonl"
        output_path.write_text("\n".join(json.dumps(item) for item in formatted), encoding="utf-8")
        print(f"Successfully formatted and saved {len(formatted)} items to {output_path}")

    except Exception as e:
        print(f"Error in format_dataset: {str(e)}")
        raise

if __name__ == "__main__":
    format_dataset()