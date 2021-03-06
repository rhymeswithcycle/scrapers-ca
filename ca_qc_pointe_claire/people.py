from pupa.scrape import Scraper

from utils import lxmlize, CanadianLegislator as Legislator

import re

COUNCIL_PAGE = 'http://www.ville.pointe-claire.qc.ca/en/city-hall-administration/your-council/municipal-council.html'


class PointeClairePersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    mayor = page.xpath('.//div[@class="item-page clearfix"]//table[1]//p')[1]
    name = mayor.xpath('.//strong/text()')[0]

    p = Legislator(name=name, post_id='Pointe-Claire', role='Maire')
    p.add_source(COUNCIL_PAGE)

    phone = re.findall(r'[0-9]{3}[ -][0-9]{3}-[0-9]{4}', mayor.text_content())[0].replace(' ', '-')
    p.add_contact('voice', phone, 'legislature')
    yield p

    rows = page.xpath('//tr')
    for i, row in enumerate(rows):
      if i % 2 == 0:
        continue
      councillors = row.xpath('./td')
      for j, councillor in enumerate(councillors):
        name = councillor.text_content()
        # rows[i + 1].xpath('.//td//a[contains(@href, "maps")]/text()')[j] # district number
        district = rows[i + 1].xpath('.//td/p[1]/text()')[j].replace(' / ', '/')

        p = Legislator(name=name, post_id=district, role='Conseiller')
        p.add_source(COUNCIL_PAGE)
        p.image = councillor.xpath('.//img/@src')[0]

        phone = re.findall(r'[0-9]{3}[ -][0-9]{3}-[0-9]{4}', rows[i + 1].xpath('.//td')[j].text_content())[0].replace(' ', '-')

        p.add_contact('voice', phone, 'legislature')

        yield p
