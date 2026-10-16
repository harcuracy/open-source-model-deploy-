"""Cloud-side script to download model weights directly into the persistent volume."""
import os
import sys

def main():
    repo_id = os.getenv("HF_REPO_ID", "unsloth/Qwen3.8-27B-GGUF")
    filename = os.getenv("HF_FILENAME", "Qwen3.8-27B-GGUF-Q8_0.gguf")
    destination = os.getenv("MODEL_DIR", "/models")

    target_path = os.path.join(destination, filename)
    if os.path.exists(target_path):
        print(f"Model already exists at {target_path}")
        return

    print(f"Downloading {filename} from {repo_id} to {destination}...")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "huggingface_hub"])
        from huggingface_hub import hf_hub_download

    os.makedirs(destination, exist_ok=True)
    downloaded_path = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=destination,
        local_dir_use_symlinks=False,
    )
    print(f"Successfully downloaded model to: {downloaded_path}")

if __name__ == "__main__":
    main()
