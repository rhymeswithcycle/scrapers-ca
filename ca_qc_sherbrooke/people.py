from pupa.scrape import Scraper

from utils import lxmlize, CanadianLegislator as Legislator

import re

COUNCIL_PAGE = 'http://www.ville.sherbrooke.qc.ca/mairie-et-vie-democratique/conseil-municipal/elus-municipaux/'


class SherbrookePersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//div[@id="c2087"]//a')
    for councillor in councillors:
      name = councillor.text_content()
      url = councillor.attrib['href']
      page = lxmlize(url)
      if 'Maire' in page.xpath('//h2/text()')[0]:
        district = 'Sherbrooke'
        role = 'Maire'
      else:
        district = page.xpath('//div[@class="csc-default"]//a[@target="_blank"]/text()')[0].replace('district', '').replace('Domaine Howard', 'Domaine-Howard').strip()
        role = 'Conseiller'
      if district in ('de Brompton', 'de Lennoxville'):
        district = district.replace('de ', '')
      p = Legislator(name=name, post_id=district, role=role)
      p.add_source(COUNCIL_PAGE)
      p.add_source(url)
      p.image = page.xpath('//div[@class="csc-textpic-image csc-textpic-last"]//img/@src')[0]
      parts = page.xpath('//li[contains(text(), "phone")]/text()')[0].split(':')
      note = parts[0]
      phone = parts[1]
      p.add_contact(note, phone, note)
      email = page.xpath('//a[contains(@href, "mailto:")]/@href')
      if email:
        email = email[0].split(':')[1]
        p.add_contact('email', email, None)
      if district == 'Brompton':
        p.add_extra('boundary_url', '/boundaries/sherbrooke-boroughs/brompton/')
      elif district == 'Lennoxville':
        p.add_extra('boundary_url', '/boundaries/sherbrooke-boroughs/lennoxville/')
      yield p
