# coding: utf-8
from utils import CanadianJurisdiction


class Manitoba(CanadianJurisdiction):
  jurisdiction_id = u'ocd-jurisdiction/country:ca/province:mb/legislature'
  geographic_code = 46
  division_name = u'Manitoba'
  name = u'Legislative Assembly of Manitoba'
  url = 'http://www.gov.mb.ca/legislature/'
  parties = [
      {'name': 'New Democratic Party of Manitoba'},
      {'name': 'Progressive Conservative Party of Manitoba'},
      {'name': 'Manitoba Liberal Party'},
      {'name': 'Independent'},
  ]
