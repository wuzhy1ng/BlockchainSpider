import urllib.parse


class QueryURLBuilder:
    def __init__(self, original_url: str):
        self.original_url = original_url

    def get(self, args: dict) -> str:
        args = {str(k): str(v) for k, v in args.items()}
        return '?'.join([
            self.original_url,
            urllib.parse.urlencode(args)
        ])


class RouterURLBuiler:
    def __init__(self, original_url: str):
        self.original_url = original_url

    def get(self, args: list) -> str:
        args = [str(arg) for arg in args]
        return urllib.parse.urljoin(
            self.original_url,
            '/'.join(args)
        )
