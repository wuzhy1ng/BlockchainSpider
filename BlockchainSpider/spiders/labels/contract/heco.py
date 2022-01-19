from BlockchainSpider.spiders.labels.contract.eth import LabelsContractETHSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class LabelsContractHECOSpider(LabelsContractETHSpider):
    name = 'labels.contract.heco'
    net = 'heco'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.base_ui_url = 'https://hecoinfo.com/'
        self.base_api_url = 'https://api.hecoinfo.com/api'
        self.apikey_bucket = JsonAPIKeyBucket('heco')
