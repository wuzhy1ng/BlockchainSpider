from typing import Dict

import scrapy


class ContextualItem(scrapy.Item):
    def __init__(self, *args, **kwargs):
        self._cb_kwargs = {}
        if kwargs.get('cb_kwargs'):
            self._cb_kwargs = kwargs.pop('cb_kwargs')
        super().__init__(*args, **kwargs)

    def set_context_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            self._cb_kwargs[k] = v

    def get_context_kwargs(self) -> Dict:
        return self._cb_kwargs
