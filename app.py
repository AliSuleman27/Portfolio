from flask import Flask, render_template, json
import os
import requests
from datetime import datetime
from flask_caching import Cache

app = Flask(__name__)

# Configure cache
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',  # For development - use 'redis' or 'memcached' in production
    'CACHE_DEFAULT_TIMEOUT': 3600  # Cache for 1 hour (3600 seconds)
})

# Load resume data
with open('data/resume.json') as f:
    resume_data = json.load(f)
@cache.memoize(timeout=3600)  # Cache this function's result for 1 hour
def get_github_stats(username):
    try:
        # Get user info
        user_url = f"https://api.github.com/users/{username}"
        user_response = requests.get(user_url)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Get contribution data
        events_url = f"https://api.github.com/users/{username}/events/public"
        events_response = requests.get(events_url)
        events_response.raise_for_status()
        events_data = events_response.json()
        
        # Count push events (which contain commits)
        total_commits = sum(1 for event in events_data if event['type'] == 'PushEvent')
        
        # Get starred repositories count
        stars_url = f"https://api.github.com/users/{username}/starred"
        stars_response = requests.get(stars_url)
        stars_response.raise_for_status()
        starred_repos = len(stars_response.json())
        
        # Get primary language from most popular repo
        repos_url = f"https://api.github.com/users/{username}/repos?sort=stars&direction=desc"
        repos_response = requests.get(repos_url)
        repos_response.raise_for_status()
        repos_data = repos_response.json()
        
        primary_language = None
        if repos_data:
            # Get the most starred repo's primary language
            most_starred_repo = repos_data[0]
            if most_starred_repo['language']:
                primary_language = most_starred_repo['language']
            else:
                # Fallback to checking all repos if primary language isn't set
                for repo in repos_data:
                    if repo['language']:
                        primary_language = repo['language']
                        break
        
        # Prepare the stats
        github_stats = {
            'account_details': {
                'username': user_data.get('login'),
                'name': user_data.get('name'),
                'avatar_url': user_data.get('avatar_url'),
                'profile_url': user_data.get('html_url'),
                'join_date': datetime.strptime(user_data.get('created_at'), '%Y-%m-%dT%H:%M:%SZ').strftime('%B %Y'),
                'starred_repos': starred_repos,
                'primary_language': primary_language or 'Python'  # Default to Python if none found
            },
            'followers': user_data.get('followers', 0),
            'public_repos': user_data.get('public_repos', 0),
            'total_contributions': total_commits
        }
        
        return github_stats
    except Exception as e:
        print(f"Error fetching GitHub stats: {e}")
        return None

@app.route('/')
def index():
    github_stats = get_github_stats('AliSuleman27')
    return render_template('index.html', resume=resume_data, github_stats=github_stats)

if __name__ == '__main__':
    app.run(debug=True)