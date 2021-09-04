import urllib.parse


class URLBuilder:
    def __init__(self, original_url: str):
        self.original_url = original_url

    def get(self, args: dict) -> str:
        return '?'.join([
            self.original_url,
            urllib.parse.urlencode(args)
        ])
