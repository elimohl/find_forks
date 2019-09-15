#!/usr/bin/env python3


import os
import argparse
from argparse import ArgumentParser
import getpass
import re
from time import time, sleep
from collections import deque

from tqdm import tqdm
import github
import requests


AUTHENTICATED_LIMIT = 5000
UNAUTHENTICATED_LIMIT = 60


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
    if not username or not password:
        rate_limit = UNAUTHENTICATED_LIMIT
        print('Warning! Github rate limit is only 60'
              'requests per hour for unauthenticated requests.')
    else:
        rate_limit = AUTHENTICATED_LIMIT

    g = github.Github(username, password)
    repo = g.get_repo(repo_name)
    forks = repo.get_forks()
    if isinstance(forks, github.Repository.Repository):
        print("Unusual case")
        print(forks.html_url)
    else:
        forks_and_stars = []
        request_times = deque()

        for fork in tqdm(forks, total=repo.forks_count):
            current_time = time()
            print(current_time)
            for t in request_times:
                if current_time - t > 3600:
                    request_times.popleft()
                else:
                    break
            request_times.append(current_time)

            print(len(request_times))
            if len(request_times) >= rate_limit:
                print(len(request_times), 'SLEEP')
                sleep(3600 - (current_time - request_times[0]))

            if is_ahead(fork.html_url):
                forks_and_stars.append((fork.html_url, fork.stargazers_count))

        if not forks_and_stars:
            print('There are no non-trivial forks')
            return

        forks_and_stars.sort(key=lambda x: x[1], reverse=True)
        print('Forks\tStars')
        for fork, star in forks_and_stars:
            print(fork, star, sep='\t')


if __name__ == '__main__':
    parser = ArgumentParser(description="Script to find non-trivial forks."
                            "Note that rate limit is 5000 requests per hour"
                            "for authenticated requests and 60 requests per hour for"
                            "unauthenticated requests."
                            "So if you need to check forks of really popular"
                            "repository it will be better to authenticate."
                            "For this you can use either arguments or"
                            "GITHUB_USERNAME and GITHUB_PASSWORD environment variables."
                            )
    parser.add_argument('repo_name',
                        help='parent repostory full name (owner/repo)')
    parser.add_argument('-u', '--username',
                        help='authenticated requests get a higher rate limit')
    parser.add_argument('-p', '--password', action=Password, nargs='?',
                        help="you don't need to enter the password at a command line;"
                        "just type -p and you will get a prompt.")

    args = parser.parse_args()
    username = args.username or os.environ.get('GITHUB_USERNAME', None)
    password = args.password or os.environ.get('GITHUB_PASSWORD', None)

    find_nice_forks(args.repo_name, username, password)
