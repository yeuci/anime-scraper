 #!/usr/bin/env python
 # -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from pprint import pprint
from urlparse import urlparse

import argparse
import csv
import mechanize
import requests
import sys

reload(sys)
sys.setdefaultencoding('utf8')

BASE_URL = 'https://gogoanimes.tv'
url = BASE_URL + '/sub-category/spring-2018-anime?page=1'

def init_mechanize():

    br = mechanize.Browser()
    br.set_handle_robots(False)   # ignore robots
    br.set_handle_refresh(False)  # can sometimes hang without this
    br.addheaders = [('User-agent', 'Firefox')]

    return br

def get_movie_details(url):

    response = br.open(url)
    bs = BeautifulSoup(response.read(), 'html.parser')

    # Get movie id, episode start and end
    movie_id = bs.find('input', attrs={'id': 'movie_id'})['value']
    ep_page = bs.find('ul', attrs={'id': 'episode_page'})

    ep_start = 0
    ep_end   = 0

    if ep_page:
        ep_link = ep_page.find('a')

        if ep_link:
            ep_start = ep_link['ep_start']
            ep_end   = ep_link['ep_end']

    return movie_id, ep_start, ep_end

def get_episode_links(ep_start, ep_end, movie_id):
    # Get episode links via API call
    url = BASE_URL + '/load-list-episode?ep_start={}&ep_end={}&id={}&default_ep=0'.format(ep_start, ep_end, movie_id)
    response = requests.get(url)

    bs = BeautifulSoup(response.text, 'html.parser')
    ep_links = [ l['href'].strip() for l in bs.find_all('a', href=True)]

    return ep_links

def get_episode_videos(url):

    response = requests.get(url)
    bs = BeautifulSoup(response.text, 'html.parser')
    multi_link = bs.find('div', attrs={'class': 'anime_muti_link'})

    videos = [ l['data-video'] for l in multi_link.find_all('a') if 'streaming' not in l['data-video'] ]

    return videos


if __name__ == "__main__":

    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--url', required=True, type = str,  help="(Required) Specify Page URL to scrape")
    args = parser.parse_args()
    url  = args.url

    o = urlparse(url)

    page = o.query.split('=')[1]
    scat = o.path.split('/')[2]

    filename = 'movies-{}-p{}.csv'.format(scat, page)

    with open(filename, 'wb') as csvfile:

        writer = csv.writer(csvfile, delimiter=',', quotechar='|')

        # Write header
        writer.writerow(['Title', 'Episode', 'Site 1', 'Site 2', 'Site 3', 'Site 4', 'Site 5', 'Site 6'])

        br = init_mechanize()
        response = br.open(url)

        bs    = BeautifulSoup(response.read(), 'html.parser')
        main  = bs.find('div', attrs={'class': 'main_body'})
        items = main.find_all('li')

        for item in items:
            a = item.find('a', href=True)
            link = a['href']

            # Skip this link, doesn't contain valid page
            if 'category' not in link:
                continue

            title = a['title']

            # Get movie details
            movie_id, ep_start, ep_end = get_movie_details(BASE_URL + link)

            # Get episode links
            ep_links = get_episode_links(ep_start, ep_end, movie_id)

            # Get videos for each episode link
            for ep_link in ep_links:

                # Get episode number
                episode = ep_link[-1]

                # Get episode videos
                videos = get_episode_videos(BASE_URL + ep_link)

                row = [title, episode]
                row.extend(videos)

                # Debug, show data
                pprint(row)
                sys.stdout.flush()

                # Write this row to csv
                writer.writerow(row)
                csvfile.flush()