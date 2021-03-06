from pupa.scrape import Scraper

from utils import lxmlize, CanadianLegislator as Legislator

import re

COUNCIL_PAGE = 'http://www.villagesenneville.qc.ca/fr/membres-du-conseil-municipal'


class SennevillePersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//div[@class="field-item even"]//tr')
    for councillor in councillors:
      district = councillor.xpath('./td[1]//strong/text()')[0].replace('no. ', '')
      role = 'Conseiller'
      if 'Maire' in district:
        district = 'Senneville'
        role = 'Maire'
      name = councillor.xpath('./td[2]//p//text()')[0].title()
      email = councillor.xpath('.//a[contains(@href, "mailto:")]/@href')[0]
      p = Legislator(name=name, post_id=district, role=role)
      p.add_source(COUNCIL_PAGE)
      try:
          p.image = councillor.xpath('.//img/@src')[0]
      except IndexError:
          pass
      p.add_contact('email', email, None)
      yield p
