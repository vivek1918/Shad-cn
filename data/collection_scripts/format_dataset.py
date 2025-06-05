import json
from pathlib import Path

def format_dataset():
    try:
        # Create processed directory if it doesn't exist
        processed_dir = Path("data/processed/")
        processed_dir.mkdir(parents=True, exist_ok=True)

        # Load raw data from different sources with error handling
        raw_files = {
            "magicui": "data/raw/magicui_full.json",  # Changed from magicui.json to magicui_full.json
            "aceternity": "data/raw/aceternity.json"
        }

        combined_data = []
        for name, file_path in raw_files.items():
            try:
                path = Path(file_path)
                if not path.exists():
                    print(f"Warning: Raw data file not found, skipping: {file_path}")
                    continue
                
                data = json.loads(path.read_text(encoding="utf-8"))
                
                # Handle both the full data format and summary format
                if isinstance(data, dict) and "components" in data:
                    # This is the summary format from magicui_full.json
                    combined_data.extend(data["components"])
                else:
                    # Regular format
                    combined_data.extend(data)
                    
                print(f"Successfully loaded {len(data)} items from {name}")
            except Exception as e:
                print(f"Error loading {name} data: {str(e)}")
                continue  # Continue with next file instead of raising

        # Format for fine-tuning
        formatted = []
        for item in combined_data:
            try:
                # Handle both direct items and JSON strings in 'completion'
                if isinstance(item, str):
                    item = json.loads(item)
                
                prompt = item.get("prompt", "")
                completion = item.get("completion", "")
                
                if not prompt or not completion:
                    print(f"Skipping item with missing prompt/completion: {item}")
                    continue
                    
                formatted.append({
                    "text": f"<|prompt|>{prompt}<|completion|>{completion}<|endoftext|>"
                })
            except (KeyError, json.JSONDecodeError) as e:
                print(f"Error processing item: {str(e)}")
                continue  # Skip malformed items

        # Save the formatted dataset
        output_path = processed_dir / "dataset.jsonl"
        with output_path.open("w", encoding="utf-8") as f:
            for item in formatted:
                f.write(json.dumps(item) + "\n")
                
        print(f"Successfully formatted and saved {len(formatted)} items to {output_path}")

    except Exception as e:
        print(f"Error in format_dataset: {str(e)}")
        raise

if __name__ == "__main__":
    format_dataset()