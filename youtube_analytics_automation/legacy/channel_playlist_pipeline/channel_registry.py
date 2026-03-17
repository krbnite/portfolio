class YouTubeChannelRegistry():
    """Registry of YouTube channels to be scraped. Contains methods to add channels to registry."""
    #--------------------------------------------------------------------
    def __init__(self):
        self.title_to_id = {
        'ChannelName01': 'channel_id_01',
        'ChannelName02': 'channel_id_02',
        'ChannelName03': 'channel_id_03',
        }
        self.id_to_title = {self.title_to_id[title]: title for title in self.title_to_id}
        self.cids = list(self.id_to_title.keys())
        self.titles = list(self.id_to_title.values())
    #--------------------------------------------------------------------
    def add_channel(self, title, cid):
        """
        Add channel to current dict by inputting cname, cid.
        """
        self.title_to_id[title] = cid
        self.id_to_title[cid] = title
        self.cids = list(self.id_to_title.keys())
        self.titles = list(self.id_to_title.values())
        self.attrs = ['channel_id', 'cids', 'titles']