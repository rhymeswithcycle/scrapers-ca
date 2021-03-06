from pupa.scrape import Scraper

from utils import lxmlize, CanadianLegislator as Legislator

import re

COUNCIL_PAGE = 'http://www.thunderbay.ca/City_Government/Your_Council.htm'


class ThunderBayPersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    councillors = page.xpath('//a[contains(@title, "Profile")][1]/@href')
    for councillor in councillors:
      page = lxmlize(councillor)
      info = page.xpath('//table/tbody/tr/td[2]')[0]

      for br in info.xpath('*//br'):
        br.tail = '\n' + br.tail if br.tail else '\n'
      lines = [line.strip() for line in info.text_content().split('\n') if line.strip()]
      text = '\n'.join(lines)
      name = lines[0].replace('Councillor ', '').replace('Mayor ', '')

      if lines[1].endswith(' Ward'):
        district = lines[1].replace(' Ward', '')
        role = 'Councillor'
      elif lines[1] == 'At Large':
        district = 'Thunder Bay'
        role = 'Councillor'
      else:
        district = 'Thunder Bay'
        role = 'Mayor'
      name = name.replace('Councillor', '').replace('At Large', '').replace('Mayor', '').strip()

      p = Legislator(name=name, post_id=district, role=role)
      p.add_source(COUNCIL_PAGE)
      p.add_source(councillor)

      p.image = page.xpath('//td[@valign="top"]/img/@src')[0]

      address = ', '.join(info.xpath('./p/text()')[0:2]).strip()
      address = re.sub(r'\s{2,}', ' ', address)

      p.add_contact('address', address, 'legislature')

      contacts = info.xpath('./p[2]/text()')
      for contact in contacts:
        contact_type, contact = contact.split(':')
        contact = contact.replace('(1st)', '').replace('(2nd)', '').strip()
        if 'Fax' in contact_type:
          p.add_contact('fax', contact, 'legislature')
        elif 'Email' in contact_type:
          break
        else:
          p.add_contact('voice', contact, contact_type)

      email = info.xpath('.//a[contains(@href, "mailto:")]')[0].text_content()
      p.add_contact('email', email, None)

      yield p
