#!/usr/bin/env python3


import os
import argparse
from argparse import ArgumentParser
import getpass
import re
from time import sleep

from tqdm import tqdm
import github
from github.GithubException import RateLimitExceededException
import requests


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


def find_nice_forks(repo_name, username, password, sleep_interval):
    success = False
    while not success:
        try:
            g = github.Github(username, password)
            repo = g.get_repo(repo_name)
            forks = repo.get_forks()
            success = True
        except RateLimitExceededException:
            print(f'Sleep for {sleep_interval} seconds because of rate limit.')
            sleep(sleep_interval)

    if isinstance(forks, github.Repository.Repository):
        print("Unusual case")
        print(forks.html_url)
    else:
        forks_and_stars = []
        for fork in tqdm(forks, total=repo.forks_count):
            success = False
            while not success:
                try:
                    if is_ahead(fork.html_url):
                        forks_and_stars.append((fork.html_url, fork.stargazers_count))
                    success = True
                except RateLimitExceededException:
                    print(f'Sleep for {sleep_interval} seconds because of rate limit.')
                    sleep(sleep_interval)
        if not forks_and_stars:
            print('There are no non-trivial forks')
            return
        forks_and_stars.sort(key=lambda x: x[1], reverse=True)
        print('Forks\tStars')
        for fork, star in forks_and_stars:
            print(fork, star, sep='\t')


if __name__ == '__main__':
    parser = ArgumentParser(description="Script to find non-trivial forks. "
                            "Note that rate limitis is 5000 requests per hour "
                            "for authenticated requests and 60 requests per hour for "
                            "unauthenticated requests. "
                            "So if you need to check forks of really popular "
                            "repository it will be better to authenticate. "
                            "For this you can use either arguments or "
                            "GITHUB_USERNAME and GITHUB_PASSWORD environment variables. "
                            )
    parser.add_argument('repo_name',
                        help='parent repostory full name (owner/repo)')
    parser.add_argument('-u', '--username',
                        help='authenticated requests get a higher rate limit')
    parser.add_argument('-p', '--password', action=Password, nargs='?',
                        help="you don't need to enter the password at a command line;"
                        "just type -p and you will get a prompt.")
    parser.add_argument('-s', '--sleep-interval', type=float, default=200,
                        help='seconds to sleep when rate limit exceeded')

    args = parser.parse_args()
    username = args.username or os.environ.get('GITHUB_USERNAME', None)
    password = args.password or os.environ.get('GITHUB_PASSWORD', None)

    find_nice_forks(args.repo_name, username, password, args.sleep_interval)
