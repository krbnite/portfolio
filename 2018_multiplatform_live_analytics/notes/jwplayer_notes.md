
## Signing In (Dashboard/GUI)

1. Go to https://dashboard.jwplayer.com
   - Enter email and password

## Some Notes

On the analytics team, we are not really using many of the features,
e.g., adding new external URLs or uploading videos. Other people
do that. Our use of JWP is to collect the website data, e.g.,
page traffic, video views, etc.

## API

There is a [JWP python package](https://github.com/jwplayer/jwplatform-py)
available on GitHub. If you prefer this method of data access, then you
must obtain your account's `API_KEY` and `API_SECRET`, which can be found
in the JWP Dashboard/GUI under the account tab.

There is also a [command line API](https://github.com/rmnl/clack), which
can give you more freedom (e.g., if you want to do an OS call from R,
or some other computing environment).
