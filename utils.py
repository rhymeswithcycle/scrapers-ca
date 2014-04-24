# coding: utf-8
import csv
from ftplib import FTP
import re
from io import StringIO
from urllib.parse import urlparse

import lxml.html
import requests
from scrapelib import Scraper as Scrapelib
from pupa.scrape import Scraper, Jurisdiction, Legislator
from pupa.models import Membership, Person

import patch

CONTACT_DETAIL_TYPE_MAP = {
  'Address': 'address',
  'bb': 'cell',
  'bus': 'voice',
  'Bus': 'voice',
  'Bus.': 'voice',
  'Business': 'voice',
  'Cell': 'cell',
  'Cell Phone': 'cell',
  'Email': 'email',
  'Fax': 'fax',
  'Home': 'voice',
  'Home Phone': 'voice',
  'Home Phone*': 'voice',
  'Office': 'voice',
  'ph': 'voice',
  'Phone': 'voice',
  'Res': 'voice',
  'Res/Bus': 'voice',
  'Residence': 'voice',
  'Téléphone (bureau)': 'voice',
  'Téléphone (cellulaire)': 'cell',
  'Téléphone (résidence)': 'voice',
  'Téléphone (résidence et bureau)': 'voice',
  'Voice Mail': 'voice',
  'Work': 'voice',
}
# In Newmarket, for example, there are both "Phone" and "Business" numbers.
CONTACT_DETAIL_NOTE_MAP = {
  'Address': 'legislature',
  'bb': 'legislature',
  'bus': 'office',
  'Bus': 'office',
  'Bus.': 'office',
  'Business': 'office',
  'Cell': 'legislature',
  'Cell Phone': 'legislature',
  'Email': None,
  'Fax': 'legislature',
  'Home': 'residence',
  'Home Phone': 'residence',
  'Home Phone*': 'residence',
  'ph': 'legislature',
  'Phone': 'legislature',
  'Office': 'legislature',
  'Res': 'residence',
  'Res/Bus': 'office',
  'Residence': 'residence',
  'Téléphone (bureau)': 'legislature',
  'Téléphone (cellulaire)': 'legislature',
  'Téléphone (résidence)': 'residence',
  'Téléphone (résidence et bureau)': 'legislature',
  'Voice Mail': 'legislature',
  'Work': 'legislature',
}


class CanadianJurisdiction(Jurisdiction):
  session_details = {
    'N/A': {
      '_scraped_name': 'N/A',
    }
  }
  terms = [
    {
      'name': 'N/A',
      'sessions': ['N/A'],
      'start_year': 1900,
      'end_year': 2030,
    }
  ]

  def __init__(self):
    for scraper_type in ('bills', 'events', 'people', 'speeches', 'votes'):
      try:
        __import__(self.__module__ + '.' + scraper_type)
      except ImportError as e:
        if "No module named '%s.%s'" % (self.__module__, scraper_type) in e.args:
          pass
        else:
          raise
      else:
        self.provides.append(scraper_type)

  def get_scraper(self, term, session, scraper_type):
    if scraper_type in self.provides:
      class_name = self.__class__.__name__ + {
        'bills': 'Bill',
        'events': 'Event',
        'people': 'Person',
        'speeches': 'Speech',
        'votes': 'Vote',
      }[scraper_type] + 'Scraper'
      return getattr(__import__(self.__module__ + '.' + scraper_type, fromlist=[class_name]), class_name)

  def scrape_session_list(self):
    return ['N/A']


class CanadianLegislator(Legislator):

  def __init__(self, name, post_id, **kwargs):
    super(CanadianLegislator, self).__init__(clean_name(name), clean_string(post_id), **kwargs)
    for k, v in kwargs.items():
      if isinstance(v, str):
        setattr(self, k, clean_string(v))

  def __setattr__(self, name, value):
    if name == 'gender':
      if value == 'M':
        value = 'male'
      elif value == 'F':
        value = 'female'
    super(CanadianLegislator, self).__setattr__(name, value)

  def add_link(self, url, note=None):
      if url.startswith('www.'):
        url = 'http://%s' % url
      if re.match(r'\A@[A-Za-z]+\Z', url):
        url = 'https://twitter.com/%s' % url[1:]

      self.links.append({"note": note, "url": url})

  def add_contact(self, type, value, note):
    if type:
      type = clean_string(type)
    if note:
      note = clean_string(note)
    if type in CONTACT_DETAIL_TYPE_MAP:
      type = CONTACT_DETAIL_TYPE_MAP[type]
    if note in CONTACT_DETAIL_NOTE_MAP:
      note = CONTACT_DETAIL_NOTE_MAP[note]

    type = type.lower()

    if type in ('text', 'voice', 'fax', 'cell', 'video', 'pager'):
      value = clean_telephone_number(clean_string(value))
    elif type == 'address':
      value = clean_address(value)
    else:
      value = clean_string(value)

    self._contact_details.append({'type': type, 'value': value, 'note': note})


# Removes _is_legislator flag and _contact_details. Used by aggregations.
# @see https://github.com/opencivicdata/pupa/blob/master/pupa/scrape/helpers.py
class AggregationLegislator(Person):
  __slots__ = ('post_id')

  def __init__(self, name, post_id, **kwargs):
    super(AggregationLegislator, self).__init__(clean_name(name), **kwargs)
    self.post_id = clean_string(post_id)
    for k, v in kwargs.items():
      if isinstance(v, str):
        setattr(self, k, clean_string(v))

  def __setattr__(self, name, value):
    if name == 'gender':
      if value == 'M':
        value = 'male'
      elif value == 'F':
        value = 'female'
    super(AggregationLegislator, self).__setattr__(name, value)


whitespace_re = re.compile(r'[^\S\n]+', flags=re.U)
honorific_prefix_re = re.compile(r'\A(?:Councillor|Dr|Hon|M|Mayor|Mme|Mr|Mrs|Ms|Miss)\.? ')
honorific_suffix_re = re.compile(r', Ph\.D\Z')

table = {
  ord('​'): ' ',  # zero-width space
  ord('’'): "'",
  ord('\xc2'): " ",  # non-breaking space if mixing ISO-8869-1 into UTF-8
}

# @see https://github.com/opencivicdata/ocd-division-ids/blob/master/identifiers/country-ca/ca_provinces_and_territories.csv
# @see https://github.com/opencivicdata/ocd-division-ids/blob/master/identifiers/country-ca/ca_provinces_and_territories-name_fr.csv
abbreviations = {
  'Newfoundland and Labrador': 'NL',
  'Prince Edward Island': 'PE',
  'Nova Scotia': 'NS',
  'New Brunswick': 'NB',
  'Québec': 'QC',
  'Ontario': 'ON',
  'Manitoba': 'MB',
  'Saskatchewan': 'SK',
  'Alberta': 'AB',
  'British Columbia': 'BC',
  'Yukon': 'YT',
  'Northwest Territories': 'NT',
  'Nunavut': 'NU',

  'PEI': 'PE',
}


def clean_string(s):
  return re.sub(r' *\n *', '\n', whitespace_re.sub(' ', s.translate(table)).strip())


def clean_name(s):
  return honorific_suffix_re.sub('', honorific_prefix_re.sub('', clean_string(s)))


def clean_telephone_number(s):

  """
  @see http://www.noslangues-ourlanguages.gc.ca/bien-well/fra-eng/typographie-typography/telephone-eng.html
  """

  splits = re.split(r'(?:/|x|ext\.?|poste)[\s-]?(?=\b|\d)', s, flags=re.IGNORECASE)
  digits = re.sub(r'\D', '', splits[0])

  if len(digits) == 10:
    digits = '1' + digits

  if len(digits) == 11 and digits[0] == '1' and len(splits) <= 2:
    digits = re.sub(r'\A(\d)(\d{3})(\d{3})(\d{4})\Z', r'\1-\2-\3-\4', digits)
    if len(splits) == 2:
      return '%s x%s' % (digits, splits[1])
    else:
      return digits
  else:
    return s


def clean_address(s):

  """
  Corrects the postal code, abbreviates the province or territory name, and
  formats the last line of the address.
  """

  # The letter "O" instead of the numeral "0" is a common mistake.
  s = re.sub(r'\b[A-Z][O0-9][A-Z]\s?[O0-9][A-Z][O0-9]\b', lambda x: x.group(0).replace('O', '0'), s)
  for k, v in abbreviations.items():
      s = re.sub(r'[,\n ]+\(?' + k + r'\)?(?=(?:[,\n ]+Canada)?(?:[,\n ]+[A-Z][0-9][A-Z]\s?[0-9][A-Z][0-9])?\Z)', ' ' + v, s)
  return re.sub(r'[,\n ]+([A-Z]{2})(?:[,\n ]+Canada)?[,\n ]+([A-Z][0-9][A-Z])\s?([0-9][A-Z][0-9])\Z', r' \1  \2 \3', s)


def lxmlize(url, encoding='utf-8', user_agent=requests.utils.default_user_agent()):
  scraper = Scrapelib(follow_robots=False, requests_per_minute=0)
  scraper.user_agent = user_agent
  entry = scraper.urlopen(url)
  if encoding != 'utf-8' or not isinstance(entry, str):
    entry = entry.encode(encoding)
  page = lxml.html.fromstring(entry)
  meta = page.xpath('//meta[@http-equiv="refresh"]')
  if meta:
    _, url = meta[0].attrib['content'].split('=', 1)
    return lxmlize(url, encoding)
  else:
    page.make_links_absolute(url)
    return page


def csv_reader(url, header=False, encoding='utf-8', **kwargs):
  result = urlparse(url)
  if result.scheme == 'ftp':
    data = StringIO()
    ftp = FTP(result.hostname)
    ftp.login(result.username, result.password)
    ftp.retrbinary('RETR %s' % result.path, lambda block: data.write(str(block, encoding=encoding)))
    ftp.quit()
    data.seek(0)
  else:
    data = StringIO(str(requests.get(url, **kwargs).content, encoding=encoding))
  if header:
    return csv.DictReader(data)
  else:
    return csv.reader(data)
