#!/usr/bin/python
# -*- coding: utf-8  -*-
'''

transfer images from Commons to Estonian Wikipedia
from category http://commons.wikimedia.org/wiki/Category:Move_to_Estonian_Wikipedia

Usage:
python commons2etwiki.py

'''

import sys
sys.path.append("/home/kentaur/py/pywikipedia")
import wikipedia as pywikibot
import re, catlib, pagegenerators
import myimagetransfer


def transferImage2Etwiki(cImagePage):
    #imagetransfer.py -family:commons -lang:commons "File:Johann-skytte.JPG" -tofamily:wikipedia -tolang:et
    #if pywikibot.Page(pywikibot.getSite('commons', 'commons'), u'Image:' + self.newname).exists():
    
    gen = iter([cImagePage])
    interwiki = False
    targetLang = u'et'
    targetFamily = u'wikipedia'
    targetSite = pywikibot.Site(targetLang, targetFamily)
    moveTemplate = u'Move to et.wiki'
    transferredTemplate = u'{{Moved to et.wiki}}'
    imageIsTransferred = False

    #login as sysop to targetSite
    #targetSite.forceLogin(sysop = True)
    #print targetSite.loggedInAs(sysop = True) + "\n"
    
    #pics that are in Commons can be duplicated only by administrator
    bot = myimagetransfer.ImageTransferBot(gen, interwiki = interwiki, targetSite = targetSite)
    bot.run()
    imagePageTitle = cImagePage.title()
    wikiImagePage = pywikibot.ImagePage(targetSite, imagePageTitle)
    
    if cImagePage.getHash() == wikiImagePage.getHash():
        imageIsTransferred = True
    
    if imageIsTransferred:
        #Get a fresh copy, force to get the page so we dont run into edit conflicts
        imtxt=cImagePage.get(force=True)
    
        #Remove the moveTemplate
        imtxt = re.sub(u'\{\{' + moveTemplate + u'\}\}', u'', imtxt)

        #add transferredTemplate
        commentText = u'Image is transferred to et.wiki'
        pywikibot.showDiff(cImagePage.get(), transferredTemplate+imtxt)
        cImagePage.put(transferredTemplate + "\n" + imtxt, comment = commentText)
        

def main():
    site = pywikibot.getSite(u'commons', u'commons')
    commonsCategory = u'Category:Move_to_Estonian_Wikipedia'
    
    recurse=False
    startfrom = None
    
    cat = catlib.Category(site, commonsCategory)
    
    pages = cat.articlesList(False)
    for cImagePage in pagegenerators.PreloadingGenerator(pages,100):
        transferImage2Etwiki(cImagePage)

        
        
if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()