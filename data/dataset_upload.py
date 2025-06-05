import os
from pathlib import Path
from datasets import load_dataset
from huggingface_hub import login, HfApi

def upload_dataset():
    try:
        # Verify dataset exists
        dataset_path = Path("C:/Users/Vivek Vasani/OneDrive/Desktop/shadcn-llama-finetune/data/collection_scripts/data/processed/dataset.jsonl")
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset file not found at {dataset_path}")

        # Load dataset
        dataset = load_dataset("json", data_files=str(dataset_path), split="train")
        print(f"Loaded dataset with {len(dataset)} examples")

        # Login to Hugging Face Hub
        # Get token from environment variable or replace with your token
        hf_token = os.getenv("HF_TOKEN", "your_huggingface_token_here")
        login(token=hf_token)

        # Initialize HfApi
        api = HfApi()

        # Upload dataset
        repo_id = "vivekvasani/shadcn-components"  # Replace with your repo
        dataset.push_to_hub(repo_id, private=True)
        print(f"Dataset successfully uploaded to {repo_id}")

    except Exception as e:
        print(f"Error uploading dataset: {str(e)}")
        raise

if __name__ == "__main__":
    upload_dataset()