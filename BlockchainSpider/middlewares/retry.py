import json
import logging

from scrapy.utils.request import fingerprint

from BlockchainSpider.middlewares.defs import LogMiddleware


class UnterminatedJSONRetryMiddleware(LogMiddleware):
    def __init__(self):
        self.max_retries = 10
        self.request2cnt = dict()

    async def process_response(self, request, response, spider):
        req_finger = fingerprint(request)
        try:
            data = response.text
            json.loads(data)
            if req_finger in self.request2cnt:
                del self.request2cnt[req_finger]
            return response
        except json.decoder.JSONDecodeError:
            cnt = self.request2cnt.get(req_finger, 0) + 1
            if cnt > self.max_retries and req_finger in self.request2cnt:
                del self.request2cnt[req_finger]
                return response
            self.log(
                message='Retry request because there is an unterminated JSON ({}/{}), '
                        'the provider may be limited by TPS: {}'.format(
                    cnt, self.max_retries, request.url,
                ),
                level=logging.WARNING,
            )
            self.request2cnt[req_finger] = cnt
            return request.replace(dont_filter=True)
