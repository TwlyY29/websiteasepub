# -*- coding: utf-8 -*-

import sys, re, unicodedata

def slugify(string):
  """
  Returns the given string converted to a string that can be used for a clean
  filename. Specifically, leading and trailing spaces are removed; other
  spaces are converted to underscores; and anything that is not a unicode
  alphanumeric, dash, underscore, or dot, is removed.
  >>> get_valid_filename("john's portrait in 2004.jpg")
  'johns_portrait_in_2004.jpg'
  
  from https://github.com/django/django/blob/master/django/utils/text.py
  """
  s = string.strip().replace('–','-').replace(' ', '_').lower()
  return(re.sub(r'(?u)[^-\w.]', '', s))

def simpleslugify(string):
  keepcharacters = ('.','_')
  return "".join(c for c in string if c.isalnum() or c in keepcharacters).rstrip()

  
if __name__ == "__main__":
  print(slugify(sys.argv[1]))
  
