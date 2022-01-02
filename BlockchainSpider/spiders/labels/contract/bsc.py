from BlockchainSpider.spiders.labels.contract.eth import LabelsContractETHSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class LabelsContractBSCSpider(LabelsContractETHSpider):
    name = 'labels.contract.bsc'
    net = 'bsc'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.base_ui_url = 'https://bscscan.com'
        self.base_api_url = 'https://api.bscscan.com/api'
        self.apikey_bucket = JsonAPIKeyBucket('bsc')
