# -*- coding: utf-8 -*-

HTMLTEMPLATE = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head><title>$title</title></head>
<body>
$content
</body>
</html>
'''

BASEPATH="./"
PANDOCPATH="pandoc"
DICT=False
ATTSTOCOMPARE=['class','id']
TAGSTOPARSE=['div','article','section','main']
INDENT='--'

DCT_TITLE='title'
DCT_CLASS='classset'

TMPLT_TITLE='title'
TMPLT_CONTENT='content'

TMPFILE="{}.epubstuff.tmp.html".format(BASEPATH)

import sys,os

from slugify import slugify
import bs4 #python3
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from string import Template
from subprocess import Popen, PIPE
from urllib.parse import urlparse, urljoin, urlunparse
import ast

def makeEpubReadyHtml(url,cntclass):
  entrycontent={}
  soup = BeautifulSoup(open(url, encoding='utf-8').read(), 'html5lib')
  entrycontent[TMPLT_TITLE] = soup.find('title').text
  cntclass = set(cntclass.split()) if not isinstance(cntclass, set) else cntclass
  for d in soup.findAll(TAGSTOPARSE):
    subst = False
    for a in ATTSTOCOMPARE:
      try:
        if isinstance(d[a], list):
          if set(d[a]) == cntclass:
            #print(d)
            entrycontent[TMPLT_CONTENT] = d
            subst = True
      except:
        pass
      try:
        if isinstance(d[a], str):
          s = set()
          s.add(d[a])
          if s == cntclass:
            #print(d)
            entrycontent[TMPLT_CONTENT] = d
            subst = True
      except:
        pass
    if subst:
      return Template(HTMLTEMPLATE).substitute(entrycontent)
  return False
  
def prettyPrintDOM(soup):
  #soup = BeautifulSoup(open(FILE, encoding='utf-8').read(), 'html5lib')
  visited=[]
  str_all = ''
  for tag in soup.find_all(TAGSTOPARSE):
    if tag in visited:
      print(type(tag))
      visited.remove(tag)
      continue
    else:
      visited.append(tag)
      depth = len(tag.find_parents(TAGSTOPARSE))
      line = "{}".format(depth*INDENT)
      linelen = len(line)+2
      line = "{}> {}".format(line,tag.name)
      #print(tag.name)
      for a in ATTSTOCOMPARE:
        try:
          line = "{}\n{}{}: {}".format(line,linelen*' ',a,tag[a] if isinstance(tag[a],str) else ' '.join(tag[a]))
        except:
          pass
      str_all = "{}\n\n{}".format(str_all,line)
  return(str_all)
  
def fetchMetaFrom(url):
  #_tmpfile = '{}{}'.format(BASEPATH,TMPFILE)
  #with open(_tmpfile, 'wb') as f:
  #  curl = pycurl.Curl()
  #  curl.setopt(pycurl.URL, url)
  #  curl.setopt(pycurl.WRITEDATA, f)
  #  curl.perform()
  #  curl.close()
  #  f.close()
  #soup = BeautifulSoup(open(_tmpfile, encoding='utf-8').read(), 'html5lib')
  req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:10.0.1) Gecko/20100101 Firefox/10.0.1'})
  soup = BeautifulSoup(urlopen(req).read(), 'html5lib')
  title = soup.find('title').text
  for i in soup.find_all(['img','a']): #only absolute urls to links and images
    try:
      i['src'] = urljoin(url,i['src'])
      o = urlparse(i['src'])
      i['src'] = urlunparse(o._replace(query=""))
      del i['srcset']
    except:
      try:
        i['href'] = urljoin(url,i['href'])
      except:
        pass
  #os.rename(_tmpfile,"{}{}.html".format(BASEPATH,slugify(title)))
  with open('{}{}.html'.format(BASEPATH,slugify(title)).encode('utf-8'),'w', encoding='utf-8') as f:
    f.write(str(soup))
    f.close()
  dictpath = "{}/{}".format(BASEPATH,DICT)
  baseurl = urlparse(url).netloc
  knownhosts = {}
  if os.path.isfile(dictpath):
    with open(dictpath,'r',encoding='utf-8') as f:
       knownhosts = ast.literal_eval(f.read())
       f.close()
  classes=[]
  classesneeded = True
  if baseurl is not None and baseurl != '' and baseurl in knownhosts and DCT_TITLE not in knownhosts.get(baseurl):
    with open(dictpath,'r',encoding='utf-8') as f:
      knownhosts = ast.literal_eval(f.read())
      f.close()
      classes = knownhosts[baseurl]
      classesneeded = False
  elif DICT:
    if baseurl not in knownhosts:
      knownhosts[baseurl] = {DCT_TITLE:set()}
    knownhosts[baseurl][DCT_TITLE].add(slugify(title))
    with open(dictpath, 'w+', encoding='utf-8') as f:
      f.write(str(knownhosts))
      f.close()    
    classes = prettyPrintDOM(soup)
  #if os.path.isfile(_tmpfile):
  #  os.remove(_tmpfile)
  return classesneeded, title, classes

def makeEpub(title,cssclass,savecssclass=True):
  title = slugify(title)
  if savecssclass and DICT:
    dictpath = "{}/{}".format(BASEPATH,DICT)
    if os.path.isfile(dictpath):
      knownhosts = {}
      with open(dictpath,'r',encoding='utf-8') as f:
        knownhosts = ast.literal_eval(f.read())
        f.close()
      update = None
      for url,entry in knownhosts.items():
        if DCT_TITLE in entry and title in entry[DCT_TITLE]:
          update = url
          break
      if update is not None:
        with open(dictpath,'w',encoding='utf-8') as f:
          knownhosts.pop(update,None)
          knownhosts[update] = set(cssclass.split())
          f.write(str(knownhosts))
  htmlfile = "{}{}.html".format(BASEPATH,title).encode('utf-8')
  epubfile = "{}{}.epub".format(BASEPATH,title).encode('utf-8')
  if os.path.isfile(htmlfile):
    html = makeEpubReadyHtml(htmlfile,cssclass)
    if html is not None and html:
      with open(htmlfile,'w', encoding='utf-8') as f:
        f.write(str(html))
        f.close()
      p = Popen([PANDOCPATH, "-s", "-f", "html", "-t", "epub", "-o", epubfile , htmlfile], stdout=PIPE)
      p.communicate()
      success = (p.returncode == 0)
      return success, epubfile, htmlfile
  return False, False, False

def checkPrerequisites():
  p = Popen([PANDOCPATH, '-v'], stdout=PIPE)
  p.communicate()
  return (p.returncode == 0)

def init(_basepath=BASEPATH, _pandocpath=PANDOCPATH, _dict=DICT, _attstocompare=ATTSTOCOMPARE, _tagstoparse=TAGSTOPARSE):
  global BASEPATH, PANDOCPATH, DICT, ATTSTOCOMPARE, TAGSTOPARSE, TMPFILE
  BASEPATH = _basepath
  PANDOCPATH = _pandocpath
  DICT = _dict
  ATTSTOCOMPARE = _attstocompare
  TAGSTOPARSE = _tagstoparse
  TMPFILE="{}.epubstuff.tmp.html".format(BASEPATH)
  
def printsettings():
  print("writing epubs to\t{}\npandoc cmd to use\t{}\nusing the css-dict\t{}\ncomparing attributes\t{}\nparsing css-tags\t{}\n".format(BASEPATH,PANDOCPATH,DICT,ATTSTOCOMPARE,TAGSTOPARSE))

if __name__ == '__main__':
  
  if checkPrerequisites():
    init(#_basepath="/var/mail/epubs/", 
      #_dict="known_hosts.json",
      _attstocompare=['class','id'],
      _tagstoparse=['div','article','section','main'])
    printsettings()
    
    needcss,title,classes = fetchMetaFrom('http://www.sepiavlc.com/bares-miticos-valencianos-almuerzo/')
    success, epubfile, htmlfile = makeEpub(title,'content',savecssclass=True)
    if success:
      print("successfully written to {}".format(epubfile))
    else:
      sys.exit(1)
    
    # using dict for known css classes
    init(_dict="known_hosts.json")
      
    needcss,title,classes = fetchMetaFrom("http://www.bakadesuyo.com/2014/10/how-to-get-people-to-like-you/")
    success, epubfile, htmlfile = makeEpub(title,'blog_wrapper',savecssclass=True) 
    if success:
      print("successfully written to {}".format(epubfile))
    else:
      sys.exit(1)
    
    needcss,title,classes = fetchMetaFrom("http://www.bakadesuyo.com/2014/10/how-to-get-people-to-like-you/")
    success, epubfile, htmlfile = makeEpub(title,classes)
    if success:
      print("successfully written to {}".format(epubfile))
    else:
      sys.exit(1)
  
