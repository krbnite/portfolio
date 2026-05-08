# Written by: Kevin Urban (2017-2018)
from selenium import webdriver
import bs4
import requests
import json
from pyvirtualdisplay import Display


def get_user_token(
    username,
    password,
    headless=False,  # True:HeadlessChrome, False:Chrome
    display=False,   # True:Display, False:VirtualDisplay
    driver_path='/usr/local/share/chromedriver',
):
    """
    This function uses Selenium to obtain a user token (must provide
    username and password).

    Written By: Kevin Urban
    """

    if not display:
        vdisplay = Display(visible=0)
        vdisplay.start()

    if headless:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(driver_path, chrome_options=options)
    else:
        browser = webdriver.Chrome(driver_path)

    GraphAPIExplorer = 'https://developers.facebook.com/tools/explorer'
    browser.get(GraphAPIExplorer)
    login = browser.find_element_by_link_text('Log In')
    login.click()
    email = browser.find_element_by_name('email')
    email.send_keys(username)
    pwrd = browser.find_element_by_name('pass')
    pwrd.send_keys(password)
    login = browser.find_element_by_name('login')
    login.click()
    page = bs4.BeautifulSoup(browser.page_source, 'lxml')
    browser.quit()
    if not display:
        vdisplay.stop()
    token_element = [item for item in page.select('input[type="text"]')
        if 'placeholder' in item.attrs
        and 'Access Token' in item['placeholder']]
    token = token_element[0]['value']
    return token


def get_authorized_accounts(token):
    """
    Get all Facebook Page accounts associated with your user account's token.

    Written By: Kevin Urban
    """
    next_url = 'https://graph.facebook.com/me/accounts?access_token=' + token
    continue_paging = True
    data = []
    while continue_paging:
        req = json.loads(requests.get(next_url).text)
        data += req['data']
        try:
            next_url = req['paging']['next']
        except:
            continue_paging = False
    return data


def get_page_token(fb_accounts, token_name=''):
    """
    Return page token for a specific account in your account list generated
    by get_authorized_accounts()

    Written By: Kevin Urban
    """
    if token_name == '':
        return [item['name'] for item in fb_accounts]
    else:
        try:
            token = [item['access_token']
                for item in fb_accounts
                if item['name'].lower() == token_name.lower()][0]
            return token
        except:
            return 'Invalid Account Name'


def get_token(username, password, token_name=None):
    """
    Written By: Kevin Urban
    """
    user_token = get_user_token(username, password)
    if token_name:
        accounts = get_authorized_accounts(user_token)
        page_token = get_page_token(accounts, token_name=token_name)
        return page_token
    else:
        return user_token


def get(url, access_token):
    """
    Written By: Kevin Urban
    """
    if access_token:
        if url.find('?') > 0:
            url = url + '&access_token=' + access_token
        else:
            url = url + '?access_token=' + access_token
    return json.loads(requests.get(url).text)


#--------------------------------------------------------------
# fb_token: this is the meat of this code, e.g., in
#   ipython shell, all this code has its best use like so:
#       from api.graph_api import fb_token
#       token = fb_token(username, password)
#       token.get('me')  # etc
#--------------------------------------------------------------
class fb_token():
    """
    Written by: Kevin Urban
    """
    def __init__(self, username, password, me='user', version='v2.12'):
        self.username = username
        self.password = password
        self.user_token = get_user_token(username, password)
        accounts = get_authorized_accounts(self.user_token)
        self.accounts = accounts
        self.page_to_token = {item['name'].lower(): item['access_token']
                for item in accounts}
        self.id_to_token = {item['id'].lower(): item['access_token']
                for item in accounts}
        self.id_to_page = {item['id'].lower(): item['name'].lower()
                for item in accounts}
        self.page_to_id = {item['name'].lower(): item['id']
                for item in accounts}
        self.page_to_token['user'] = self.user_token
        self.version = version
        self.fbg = 'https://graph.facebook.com/' + self.version + '/'
        self.me = me.lower()
        self.active_token = self.page_to_token[me.lower()]

    def renew(self):
        self.__init__(self.username, self.password, self.me)

    def get(self, url, me=None):
        if me is None:
            access_token = self.active_token
        else:
            access_token = self.page_to_token[me.lower()]
        if url.find('?') > 0:
            url = self.fbg + url + '&access_token=' + access_token
        else:
            url = self.fbg + url + '?access_token=' + access_token
        return json.loads(requests.get(url).text)

    def pget(self, url, me=None):
        """
        pget is shorthand for "post get" -- basically, for very large requests,
          Facebook says you will get better performance using this.  I've used both
          get and pget, and 'pget' seems to suck whenever 'get' sucks...maybe your
          mileage will vary though. I mostly always use 'get' b/c of this.
        """
        if me is None:
            access_token = self.active_token
        else:
            access_token = self.page_to_token[me.lower()]
        if url.find('?') > 0:
            url = self.fbg + url + '&method=GET&access_token=' + access_token
        else:
            url = self.fbg + url + '?method=GET&access_token=' + access_token
        return json.loads(requests.post(url).text)

    def change_token_by_name(self, page_name):
        """
        fb_token grabs tokens for all Facebook Pages associated with your username; this
        method lets change the active token by page name (fb_token.page_to_token.keys()).
        """
        page_name = page_name.lower()
        if page_name in self.page_to_token.keys():
            self.active_token = self.page_to_token[page_name]
            self.me = page_name
        else:
            assert False, \
                'Oops: Page name is not listed in self.page_to_token.keys()'

    def change_token_by_id(self, page_id):
        """
        fb_token grabs tokens for all Facebook Pages associated with your username; this
        method lets change the active token by page id (fb_token.page_to_token.keys()).
        """
        try:
            self.active_token = self.id_to_token[page_id]
            self.me = self.id_to_page[page_id]
        except:
            assert False, \
                'Oops: You do not have rights for the given Page ID'

    def change_version(self, version):
        # Ensure that version = vx.y
        version = version.lower()
        if len(version.split('v')) == 1:
            version = 'v' + version
        if len(version.split('.')) != 2:
            print('Oops: Version must be vx.y, e.g., v2.12')
        try:
            int(''.join(version.split('v')[1].split('.')))
        except:
            print('Oops: Version must be vx.y, where x and y are integer characters,'
            'e.g., v2.12')
        # If all good, change version and root URL
        self.version = version
        self.fbg = 'https://graph.facebook.com/' + version + '/'

#--------------------------------------------------------


class ig_token(fb_token):
    """
    Instagram Graph requests require a privileged user's token, not the Facebook
    Page token.  To ensure this requirement is met, ig_token differs from fb_token
    in that it does not implement .change_token_by_x methods (i.e., the token for
    ig_token is always the user token). This token class also differs from fb_token
    in that it implements a .iget(query) method in addition to the .get(query) method,
    which is not as useful with ig_token (e.g., who cares about `me?fields=whatever`
    for your user account).  Since it is a user token we are using, "me" isn't useful
    -- instead we are always querying off the instagram business account ID edge
    (f"{iba}?fields=whatever").

    Written By: Kevin Urban
    """
    def __init__(self, username, password, me='user', version='v2.12'):
        self.username = username
        self.password = password
        self.user_token = get_user_token(username, password)
        accounts = get_authorized_accounts(self.user_token)

        # Temporary initialization so self.get() is usable in the loop below
        self.version = version
        self.fbg = 'https://graph.facebook.com/' + self.version + '/'
        self.active_token = self.user_token

        # Keep Only FB Pages w/ Associated Instagram Accounts
        ig_accounts = []
        for item in accounts:
            temp = self.get(f"{item['id']}?fields=id,name,instagram_business_account")
            if 'instagram_business_account' in temp.keys():
                iba = temp['instagram_business_account']['id']
                item['iba'] = iba
                ig_accounts.append(item)
        self.accounts = ig_accounts
        self.page_to_token = {item['name'].lower(): item['access_token']
                for item in ig_accounts}
        self.id_to_token = {item['id'].lower(): item['access_token']
                for item in ig_accounts}
        self.id_to_page = {item['id'].lower(): item['name'].lower()
                for item in ig_accounts}
        self.page_to_id = {item['name'].lower(): item['id']
                for item in ig_accounts}
        self.page_to_token['user'] = self.user_token
        self.me = me.lower()
        self.active_token = self.page_to_token[me.lower()]
        self.iba = [item['iba'] for item in self.accounts if item['name'] == self.me]
