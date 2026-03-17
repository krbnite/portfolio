import time
import requests
import bs4 
import random
import pandas as pd

#====================================================
# Requests/BeautifulSoup Tools
#====================================================
# These tools were used in previous versions. 
# Could still swap out the Data API tools with these
# if necessary in the future (e.g., if Data API is no longer
# available, or changes dramatically).
 
# Scrape a single asset: www.youtube.com/watch?v=video_id 
def scrape_ith_vidkey(latest, i):
    youtube = 'https://www.youtube.com/watch'
    vidkey={'v': latest.video_id[i]}
    page = requests.get(youtube, params=vidkey)
    # Extract metrics
    bs = bs4.BeautifulSoup(page.text, 'lxml')
    if bs.find('div', {'class': 'watch-view-count'}) is not None:
        views    = bs.find('div', {'class': 'watch-view-count'}).text
        likes    = bs.find('button', {'title': 'I like this'}).text
        dislikes = bs.find('button', {'title': 'I dislike this'}).text
        output = {
                'views': int(''.join(views.split(' ')[0].split(','))) \
                        if views[0:2].lower() != 'no' \
                        else 0,
                'likes': int(''.join(likes.split(','))) \
                        if likes != '' \
                        else 0,
                'dislikes': int(''.join(dislikes.split(','))) \
                        if dislikes != '' \
                        else 0,
                'time_scraped_est': str(datetime.now(pytz.timezone('US/Eastern'))).split('.')[0]
                #'html': page.text  # too long for Redshift
                }
    else:
        output = {'views': None, 'likes': None, 'dislikes': None,
                'time_scraped_est': str(datetime.now(pytz.timezone('US/Eastern'))).split('.')[0]
                #'html': 'This video is unavailable. Sorry about that.'
                }
    return output


# Scrape all 
def scrape_youtube(latest, max_pause=8):
    # latest already has cols video_id, title, time_uploaded
    latest['time_scraped_est'] = pd.Series([0 for i in range(0,len(latest))])
    latest['views'] = pd.Series([0 for i in range(0,len(latest))])
    latest['likes'] = pd.Series([0 for i in range(0,len(latest))])
    latest['dislikes'] = pd.Series([0 for i in range(0,len(latest))])
    youtube = 'https://www.youtube.com/watch'
    n_uploads = len(latest)
    print("Beginning scrape...")
    for i in range(n_uploads):
        page = scrape_ith_vidkey(latest, i)
        latest.loc[i,'views'] = page['views']
        latest.loc[i,'likes'] = page['likes']
        latest.loc[i,'dislikes'] = page['dislikes']
        latest.loc[i, 'time_scraped_est'] = page['time_scraped_est']

        # Wait a sec! (Or two or three)
        rand_num_of_secs = random.choice([i for i in range(1,max_pause)])
        print('Waiting %d seconds before next scrape...' % rand_num_of_secs)
        time.sleep(rand_num_of_secs)
    return latest