# coding: utf-8
from utils import CanadianJurisdiction


class PrinceEdwardIsland(CanadianJurisdiction):
  jurisdiction_id = u'ocd-jurisdiction/country:ca/province:pe/legislature'
  geographic_code = 11
  division_name = u'Prince Edward Island'
  name = u'Legislative Assembly of Prince Edward Island'
  url = 'http://www.assembly.pe.ca'
  parties = [
      {'name': u'Liberal Party of Prince Edward Island'},
      {'name': u'Progressive Conservative Party of Prince Edward Island'},
  ]

