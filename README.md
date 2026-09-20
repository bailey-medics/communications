# Communications

Post to several social media platforms from Python. Each platform lives in
its own folder under `comms/` and exposes a client class with the same
three-method interface:

- `requirements()` returns the fields `post()` accepts, the maximum text
  length and, where relevant, the maximum image size in KB.
- `name()` returns the display name of the platform.
- `post(...)` publishes the post.

## Platforms

| Platform  | Module                                | Text used                          |
| --------- | ------------------------------------- | ---------------------------------- |
| X         | `comms/x/x_client.py`                 | `short_blurb`, `image`             |
| Bluesky   | `comms/bluesky/bluesky_client.py`     | `short_blurb`, `image`, `alt_text` |
| Mastodon  | `comms/mastodon/mastodon_client.py`   | `short_blurb`, `image`, `alt_text` |
| Instagram | `comms/instagram/instagram_client.py` | `short_blurb`, `image`             |
| LinkedIn  | `comms/linkedin/linkedin_client.py`   | `long_blurb`, `image`              |
| Facebook  | `comms/facebook/facebook_client.py`   | `long_blurb`, `image`              |
| Email     | `comms/email/email_client_hold.py`    | `title`, `long_blurb`, `image`     |

Folders under `comms/in_progress/` are placeholders for platforms that are
not yet implemented.

## Installation

```bash
pip install poetry
poetry install
```

Copy `.env_example` to `.env` and fill in the credentials for the platforms
you intend to use. The LinkedIn access token can be obtained with
`comms/linkedin/linkedin_get_access_token.py`.

## Usage

Import a client and call `post()` directly:

```python
from comms.bluesky.bluesky_client import BlueskyClient

client = BlueskyClient()
client.post(
    short_blurb="Hello from Python",
    image="media/ldd-logo.png",
    alt_text="Let's Do Digital logo",
)
```

Each client module can also be run on its own from the command line for a
one-off post. See the `__main__` block at the bottom of each file for the
arguments it takes.

## TODO

- Make sure images are not too big
- add emails to all comms
- need a nice html layout for emails
- need to sometimes include previous posts (perhaps a weekly email summary on Mondays).
- need to check that all of the clients can handle messages, images, alt text missing
- can you put alt text in an email?
- Need to add code to add images to emails
- will need to consider plain text and html email bodies (eg html tags)
