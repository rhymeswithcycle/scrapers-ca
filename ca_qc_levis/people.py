# coding: utf8
from pupa.scrape import Scraper

from utils import lxmlize, CanadianLegislator as Legislator

import re
import urllib.parse
import html.parser

COUNCIL_PAGE = 'http://www.ville.levis.qc.ca/Fr/Conseil/'


class LevisPersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//table[@id="Tableau_01"]//a/@href')
    for councillor in councillors:
      page = lxmlize(councillor)
      name = page.xpath('//table[@id="table1"]//td[2]//b')[0].text_content()
      district = page.xpath('//table[@id="table1"]//td[2]//i')[0].text_content()
      if 'Maire' in district:
        district = 'Lévis'
        role = 'Maire'
      else:
        district = re.findall(r'[dD]istrict [0-9]{1,2}', district)[0]
        role = 'Conseiller'

      p = Legislator(name=name, post_id=district, role=role)
      p.add_source(COUNCIL_PAGE)
      p.add_source(councillor)
      p.image = page.xpath('//img[@alt = "Photo du membre"]/@src')[0]

      script = page.xpath('//table[@id="table1"]//td[2]//script')[0].text_content()
      email = get_email(script)
      p.add_contact('email', email, None)
      yield p


def get_email(script):
  h = html.parser.HTMLParser()
  email = h.unescape(re.search('(?<=")[^"]+', urllib.parse.unquote(''.join(re.findall("(?<=\(\')[^']+", script)))).group(0))
  return email + '@ville.levis.qc.ca'
