import os
import sys
import requests

TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def get_repos():
    print("Fetching repositories...")
    repos = []
    url = "https://api.github.com/user/repos?per_page=100"
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        repos.extend([repo['full_name'] for repo in response.json()])
        url = response.links.get('next', {}).get('url')
    return repos

def check_artifact_storage(repo):
    url = f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100"
    total_bytes = 0
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            break
        data = response.json()
        total_bytes += sum(a.get('size_in_bytes', 0) for a in data.get('artifacts', []))
        url = response.links.get('next', {}).get('url')
    
    return total_bytes / (1024 * 1024)

def run_audit():
    if not TOKEN:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)

    repos = get_repos()
    print(f"Found {len(repos)} repositories. Auditing artifact storage...\n")
    print(f"{'REPOSITORY':<45} {'ARTIFACTS (MB)'}")
    print("-" * 60)
    
    for repo in repos:
        size_mb = check_artifact_storage(repo)
        if size_mb > 0:
            print(f"{repo:<45} {size_mb:.2f} MB")

if __name__ == "__main__":
    run_audit()
