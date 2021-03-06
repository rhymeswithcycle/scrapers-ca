# coding: utf-8
from pupa.scrape import Scraper

from utils import lxmlize, CanadianLegislator as Legislator

import re

COUNCIL_PAGE = 'http://www.kelowna.ca/CM/Page159.aspx'


class KelownaPersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)
    links = page.xpath('//td[@width=720]//a[contains(text(), "Councillor") or '
                       'contains(text(), "Mayor")]')
    for link in links:
      role, name = link.text_content().replace(u'\xa0', u' ').split(' ', 1)
      url = link.attrib['href']
      page = lxmlize(url)
      photo_url = page.xpath('string(//li/img/@src)')
      phone = page.xpath('//strong')[-1].text_content()
      email = page.xpath('string(//a[starts-with(@href, "mailto:")])')

      p = Legislator(name=name, post_id='Kelowna', role=role, image=photo_url)
      p.add_source(COUNCIL_PAGE)
      p.add_source(url)
      p.add_contact('voice', phone, 'legislature')
      p.add_contact('email', email, None)
      yield p
