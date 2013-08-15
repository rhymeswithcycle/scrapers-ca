from utils import CanadianJurisdiction

class Saskatchewan(CanadianJurisdiction):
  jurisdiction_id = 'ocd-jurisdiction/country:ca/province:sk/legislature'
  geographic_code = 47
  def _get_metadata(self):
    return {
      'name': 'Saskatchewan',
      'legislature_name': 'Saskatchewan City Council',
      'legislature_url': 'http://www.municipal.gov.sk.ca/Programs-Services/Municipal-Directory-pdf',
      'provides': ['people'],
    }
