from github import Github
from datetime import datetime
POT = datetime.strptime("2020-01-29 00:00:00", '%Y-%m-%d %H:%M:%S')
ORG = "Identity"

g = Github(base_url="https://mygithub.enterprise.com/api/v3", login_or_token="-----------------your token of github----------------")


org = g.get_organization(ORG)
repos = org.get_repos()
outdated_keys=[]
# remove old key
for repo in repos:
    for key in repo.get_keys():
        if key.created_at < POT:
            print({
                "repo": repo.full_name,
                "title": key.title,
                "url": "{}/settings/keys".format(repo.html_url)
            })
