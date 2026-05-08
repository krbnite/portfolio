import pandas as pd

def get_page_fields(token, me=None, limit=50):
    """
    For a Page Node, the /likes edge lists other pages liked by the Page Node,
    whereas for most other nodes the /likes edge lists users who have liked
    the object (for these types of objects, one can get a likes count using
    summary=true).  The like count for a page is the field fan_count.
    """
    if me is None:
        me = token.me

    data = token.get('me?fields=id,name,fan_count,talking_about_count')


def get_page_albums(token, me=None, limit=50):
    """
    This generates an instantaneous snapshot of all of a Page's albums.

    token: pass in fb_token object
    limit: the default for a request is 25 and the max appears to be 50
        (despite that in the past it was apparently upwards of 500); so we
        re-default the limit to 50 in this function.
    """
    if me is None:
        me = token.me

    data = []
    next_url = 'me/albums?limit=' + str(limit)
    while next_url:
        response = token.get(next_url, me)
        data += response['data']
        try:
            next_url = response['paging']['next'].split(token.fbg)[1]
        except:
            next_url = None

    df = pd.DataFrame(columns=['page_name', 'page_id', 'album_id', 'album_name'])
    for idx in range(len(data)):
        item = data[idx]
        df.loc[idx, ['album_id', 'album_name']] = [item['id'], item['name']]

    page = token.get('me', me)
    df.page_id = page['id']
    df.page_name = page['name']

    return df


def get_page_albums_for_all_accounts(token, limit=50):
    pages = token.page_to_token.copy()
    _discard = pages.pop('user')
    df = pd.DataFrame(columns=['page_name', 'page_id', 'album_id', 'album_name'])
    for page in pages.keys():
        temp = get_page_albums(token, me=page)
        df = df.append(temp, ignore_index=True)
    return df
