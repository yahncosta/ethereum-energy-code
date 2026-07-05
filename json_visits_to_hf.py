import os

from huggingface_hub import HfApi


repo_id = "yhackspacher/ethereum-energy-data"
token = os.environ.get("HF_TOKEN")

if not token:
    raise SystemExit("Set HF_TOKEN before uploading.")

api = HfApi(token=token)
for file_name in ["out_consensus.json", "out_execution.json"]:
    api.upload_file(
        path_or_fileobj=file_name,
        path_in_repo=file_name,
        repo_id=repo_id,
        repo_type="dataset",
        commit_message=f"Add {file_name}",
    )
    print(f"Uploaded {file_name} to {repo_id}")
