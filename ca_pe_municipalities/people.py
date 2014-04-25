from pupa.scrape import Scraper
from pupa.models import Organization

from utils import lxmlize, clean_telephone_number, clean_address, AggregationLegislator as Legislator

import re

COUNCIL_PAGE = 'http://www.gov.pe.ca/mapp/municipalitites.php'


class PrinceEdwardIslandMunicipalitiesPersonScraper(Scraper):

  def get_people(self):
    page = lxmlize(COUNCIL_PAGE)

    districts = page.xpath('//div[@id="left-content" or @id="right-content"]//a')
    for district in districts:
      url = district.attrib['href']
      page = lxmlize(url)

      org = Organization(name=district.text_content() + ' Council', classification='legislature', jurisdiction_id=self.jurisdiction.jurisdiction_id)
      org.add_source(url)
      yield org

      info = page.xpath('//div[@style="WIDTH:750"]/dl')
      for contact in info:
        contact_type = contact.xpath('./dt')[0].text_content()
        contact = contact.xpath('./dd')[0].text_content().replace('(', '').replace(') ', '-')
        if 'Officials' in contact_type:
          break
        if 'Tel' in contact_type:
          phone = contact
        if 'Fac' in contact_type:
          fax = contact
        if 'Address' in contact_type:
          address = contact
        if 'Email' in contact_type:
          email = contact
        if 'Website' in contact_type:
          site = contact

      councillors = page.xpath('//div[@style="WIDTH:750"]/dl/dt[contains(text(), "Elected Officials")]/parent::dl/dd/pre/text()')[0].splitlines(True)
      for councillor in councillors:
        name = councillor.replace('(Mayor)', '').replace('(Deputy Mayor)', '').replace('(Chairperson)', '').strip()
        role = re.sub(r'\(|\)', '', councillor.replace(name, '').strip())
        if not role:
          role = 'Councillor'
        p = Legislator(name=name, post_id=district.text_content())
        p.add_source(COUNCIL_PAGE)
        p.add_source(url)
        membership = p.add_membership(org, role=role, post_id=district.text_content())
        membership.add_contact_detail('voice', clean_telephone_number(phone), 'legislature')
        membership.add_contact_detail('fax', clean_telephone_number(fax), 'legislature')
        membership.add_contact_detail('address', clean_address(address), 'legislature')
        membership.add_contact_detail('email', email, None)
        if site:
          p.add_link(site, None)
        yield p
