# coding: utf-8
from pupa.scrape import Scraper

from utils import csv_reader, CanadianLegislator as Legislator

import re

COUNCIL_PAGE = 'http://ottawa.ca/en/city-council'
COUNCIL_CSV_URL = 'http://data.ottawa.ca/en/storage/f/2013-10-29T130227/Elected-Officials-%282010-2014%29-v.3.csv'


class OttawaPersonScraper(Scraper):

  def get_people(self):
      for councillor in csv_reader(COUNCIL_CSV_URL, header=True):
        name = '%s %s' % (councillor['First name'], councillor['Last name'])
        role = councillor['Elected office']
        if role == 'Mayor':
          district = 'Ottawa'
        else:
          district = councillor['District name']

        # Correct typos. The City has been notified of the errors.
        if district == 'Knoxdale Merivale':
          district = 'Knoxdale-Merivale'
        if district == 'Rideau Vanier':
          district = 'Rideau-Vanier'
        if district == 'Orleans':
          district = 'Orléans'

        email = councillor['Email']
        address = ', '.join([councillor['Address line 1'],
                             councillor['Address line 2'],
                             councillor['Locality'],
                             councillor['Postal code'],
                             councillor['Province']])
        phone = councillor['Phone']
        photo_url = councillor['Photo URL']

        p = Legislator(name=name, post_id=district, role=role)
        p.add_source(COUNCIL_CSV_URL)
        p.add_contact('email', email, None)
        p.add_contact('address', address, 'legislature')
        p.add_contact('voice', phone, 'legislature')
        p.image = photo_url
        yield p

