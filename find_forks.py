#!/usr/bin/env python3


from argparse import ArgumentParser
import argparse, getpass
import github
import requests
from tqdm import tqdm
import re


class Password(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if values is None:
            values = getpass.getpass()
        setattr(namespace, self.dest, values)


def is_ahead(url):
    r = requests.get(url)
    if re.findall(r'This branch is \d* commits? ahead', r.text):
        return True
    return False


def find_nice_forks(repo_name, username, password):
    g = github.Github(username, password)
    repo = g.get_repo(repo_name)
    forks = repo.get_forks()
    if isinstance(forks, github.Repository.Repository):
        print("Unusual case")
        print(forks.html_url)
    else:
        forks_and_stars = [(fork.html_url, fork.stargazers_count)
                for fork in tqdm(forks, total=repo.forks_count) if is_ahead(fork.html_url)]
        if not forks_and_stars:
            print('There are no non-trivial forks')
            return
        forks_and_stars.sort(key=lambda x: x[1], reverse=True)
        print('Forks\tStars')
        for fork, star in forks_and_stars:
            print(fork, star, sep='\t')


if __name__ == '__main__':
    parser = ArgumentParser(description='Script to find non-trivial forks')
    parser.add_argument('repo_name',
                        help='parent repostory full name (owner/repo)')
    parser.add_argument('-u', '--username',
                        help='authenticated requests get a higher rate limit')
    parser.add_argument('-p', '--password', action=Password, nargs='?')

    args = parser.parse_args()
    find_nice_forks(args.repo_name, args.username, args.password)
