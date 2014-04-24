from pupa.scrape import Scraper
from pupa.models import Organization

from utils import lxmlize, AggregationLegislator as Legislator

import re
import urllib.request
import os
import subprocess

COUNCIL_PAGE = 'http://www.unsm.ca/doc_download/880-mayor-list-2013'


class NovaScotiaMunicipalitiesPersonScraper(Scraper):

  def get_people(self):
    response = urllib.request.urlopen(COUNCIL_PAGE).read()
    pdf = open('/tmp/ns.pdf', 'w')
    pdf.write(response)
    pdf.close()

    data = subprocess.check_output(['pdftotext', '/tmp/ns.pdf', '-'])
    emails = re.findall(r'(?<=E-mail: ).+', data)
    data = re.split(r'Mayor |Warden ', data)[1:]
    for i, mayor in enumerate(data):
      lines = mayor.splitlines(True)
      name = lines.pop(0).strip()
      if name == "Jim Smith":
        continue
      district = lines.pop(0).strip()
      if not re.findall(r'[0-9]', lines[0]):
        district = district + ' ' + lines.pop(0).strip()

      org = Organization(name=district + ' Municipal Council', classification='legislature', jurisdiction_id=self.jurisdiction.jurisdiction_id)
      org.add_source(COUNCIL_PAGE)
      yield org

      p = Legislator(name=name, post_id=district)
      p.add_source(COUNCIL_PAGE)
      membership = p.add_membership(org, role='Mayor', post_id=district)

      address = lines.pop(0).strip() + ', ' + lines.pop(0).strip()
      if not 'Phone' in lines[0]:
        address = address + ', ' + lines.pop(0).strip()

      if not 'Phone' in lines[0]:
        address = address + ', ' + lines.pop(0).strip()

      phone = lines.pop(0).split(':')[1].strip()
      if 'Fax' in lines.pop(0):
        fax = lines.pop(0)

      membership.add_contact_detail('address', address, 'legislature')
      membership.add_contact_detail('voice', phone, 'legislature')
      membership.add_contact_detail('fax', fax, 'legislature')
      # @todo emails are being assigned incorrectly, e.g. Town of Berwick picks
      # up Cape Breton Regional Municipality and Region of Queens Municipality
      for i, email in enumerate(emails):
        regex = name.split()[-1].lower() + '|' + '|'.join(district.split()[-2:]).replace('of', '').lower()
        regex = regex.replace('||', '|')
        matches = re.findall(r'%s' % regex, email)
        if matches:
          membership.add_contact_detail('email', emails.pop(i), None)
      yield p

    os.system('rm /tmp/ns.pdf')
