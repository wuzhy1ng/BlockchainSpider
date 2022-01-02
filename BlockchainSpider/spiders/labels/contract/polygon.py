from BlockchainSpider.spiders.labels.contract.eth import LabelsContractETHSpider
from BlockchainSpider.utils.apikey import JsonAPIKeyBucket


class LabelsContractPOLYSpider(LabelsContractETHSpider):
    name = 'labels.contract.polygon'
    net = 'polygon'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.base_ui_url = 'https://polygonscan.com/'
        self.base_api_url = 'https://api.polygonscan.com/api'
        self.apikey_bucket = JsonAPIKeyBucket('polygon')
