#!/home/ubuntu/anaconda/bin/ipython
from youtube_channel_surf import YouTubeChannelScraper
from channel_registry import YouTubeChannelRegistry
import os
from redshift_utils import connect_to_redshift

con = connect_to_redshift('user','password','host','db', port='5439')

if __name__ == '__main__':
    if 'chromedriver' not in os.listdir('/usr/local/share/'):
        print('Must download chromedriver into /usr/local/share/ directory.')
    else:
        channels = YouTubeChannelRegistry().cids
        for cid in channels:
            surf = YouTubeChannelScraper(cid, con, visual=False)
            surf.cpv_scrape = surf.get_cpv_scrape()
            surf.append_channels(surf.cpv_scrape)
            surf.append_list2chan(surf.cpv_scrape)
            surf.append_vid2list(surf.cpv_scrape)