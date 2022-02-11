import os

import scrapy

from BlockchainSpider.items import LabelItem


class LabelsOFACSpider(scrapy.Spider):
    name = 'labels.ofac'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.url_sdn = 'https://www.treasury.gov/ofac/downloads/sdn.xml'

        self.out_dir = kwargs.get('out', './data')

    def start_requests(self):
        yield scrapy.Request(
            url=self.url_sdn,
            method='GET',
        )

    def parse(self, response, **kwargs):
        response.selector.register_namespace("sdn", "http://tempuri.org/sdnList.xsd")
        for entry in response.xpath("//sdn:sdnEntry"):
            if not self._has_address(entry):
                continue

            # parse info
            uid = entry.xpath('./sdn:uid/text()').get()
            first_name = entry.xpath('./sdn:firstName/text()').get()
            last_name = entry.xpath('./sdn:lastName/text()').get()
            sdn_type = entry.xpath('./sdn:sdnType/text()').get()
            identities = list()
            for identity in entry.xpath('./sdn:idList/sdn:id'):
                id_type = identity.xpath('./sdn:idType/text()').get()
                id_number = identity.xpath('./sdn:idNumber/text()').get()
                if id_type.find('Digital Currency Address') >= 0:
                    continue
                identities.append({
                    'id_type': id_type,
                    'id_number': id_number
                })

            # bind info with addresses as items
            for identity in entry.xpath('./sdn:idList/sdn:id'):
                id_type = identity.xpath('./sdn:idType/text()').get()
                id_number = identity.xpath('./sdn:idNumber/text()').get()
                if id_type.find('Digital Currency Address') >= 0:
                    yield LabelItem(
                        net=id_type.replace('Digital Currency Address -', '').strip(),
                        label=sdn_type,
                        info={
                            'uid': uid,
                            'address': id_number,
                            'first_name': first_name,
                            'last_name': last_name,
                            'identities': identities,
                        }
                    )

    def _has_address(self, entry):
        for _id in entry.xpath('./sdn:idList/sdn:id'):
            id_type = _id.xpath('./sdn:idType/text()').get()
            if isinstance(id_type, str) and id_type.find('Digital Currency Address') >= 0:
                return True
        return False
