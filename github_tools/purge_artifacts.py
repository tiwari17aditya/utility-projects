import os
import sys
import argparse
import requests

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def purge_artifacts(repo):
    if not TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)

    print(f"Locating artifacts in repository: {repo}...")
    url = f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100"
    deleted_count = 0
    freed_mb = 0

    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Failed to fetch artifacts: {response.status_code} - {response.text}")
            break
            
        data = response.json()
        artifacts = data.get('artifacts', [])
        
        if not artifacts:
            break
            
        for artifact in artifacts:
            a_id = artifact['id']
            a_name = artifact['name']
            a_size = artifact.get('size_in_bytes', 0) / (1024 * 1024)
            
            delete_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{a_id}"
            del_resp = requests.delete(delete_url, headers=HEADERS)
            
            if del_resp.status_code == 204:
                print(f"Deleted: {a_name} ({a_size:.2f} MB)")
                deleted_count += 1
                freed_mb += a_size
            else:
                print(f"Failed to delete {a_name} (Status code: {del_resp.status_code})")
                
        url = response.links.get('next', {}).get('url')

    print("-" * 50)
    print(f"Cleanup Complete! Deleted {deleted_count} artifacts.")
    print(f"Total space freed: {freed_mb:.2f} MB")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge GitHub Actions artifacts for a given repository.")
    parser.add_argument("repo", help="Repository in owner/repo format (e.g. tiwari17aditya/pulsevector)")
    args = parser.parse_args()
    purge_artifacts(args.repo)
