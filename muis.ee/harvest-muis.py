# -*- coding: iso8859-1 -*-
"""
Bot for uploading images from www.muis.ee to Commons

Usage:
python harvest-muis.py

"""

import re, sys, os
sys.path.append("/home/kentaur/py/pywikipedia")
import wikipedia as pywikibot
import urllib
import BeautifulSoup
import upload
import time

#cats for diffrent museums
museumData = {
    ('Saaremaa Muuseum') : {
    'cat' : u'Images from the Saaremaa Museum'
    },
    ('Eesti Rahva Muuseum') : {
    'cat' : u'Images from the Estonian National Museum'
    }
}

# classes

class Image:
#Constructor with default arguments
   def __init__(self, url = u''):
     self.url = url
     self.name = u''
     self.description = u''
     self.date = u''
     self.source = u''
     self.author = u''
     self.permission = u''
     self.other_versions = u''
     self.other_fields = u''
     self.license = u''
     self.categories = []
    
   def getFullDesc(self):
    outFDesc = u'=={{int:filedesc}}==\n\
{{Information \n\
|description=%s \n\
|date=%s \n\
|source=%s \n\
|author=%s \n\
|permission=%s \n\
|other_versions=%s \n\
|other_fields=%s \n\
}} \n\
\n\
=={{int:license-header}}== \n\
%s \n\n\
' % (self.description, self.date, self.source, self.author, self.permission, self.other_versions, self.other_fields, self.license)

    for aCat in self.categories:
        outFDesc += "[[Category:%s]]\n" % (aCat,)
    
    return outFDesc

     
# functions

def getMuisUrls(inSite, inPageName):
    outUrls = []
    urlsPage = pywikibot.Page(inSite, inPageName)
    pageTxt = urlsPage.get()
    outUrls = re.findall(r"http://www.muis.ee/portaal/museaalview/\d+", pageTxt)
    
    return outUrls


def getWikiTable(inTable):
        wikiTable = "<table>\n"
        rows = inTable.findAll('tr')
        for row in rows:
            wikiTable += "<tr>\n"
            wikiTable += "<td>\n"
            cells = []
            colsH = row.findAll('th')
            for col in colsH:
                colText = " ".join(col.findAll(text=True))
                cells.append( colText )
            cols = row.findAll('td')
            for col in cols:
                colText = " ".join(col.findAll(text=True))
                cells.append( colText )
            wikiTable += " </td><td> ".join(cells)
            wikiTable += "</td></tr>\n"
        wikiTable += "</table>\n"
        
        return wikiTable

def getImage(url):
    uo = pywikibot.MyURLopener
    file = uo.open(url)
    soup = BeautifulSoup.BeautifulSoup(file.read())
    file.close()
    outImage = Image()

    imgTag = soup.find("img", { "class" : "imageWithCaption" })
    link = imgTag.get("src", imgTag.get("href", None))
    if link:
        outImage.url = urllib.basejoin(url, link)
        caption = soup.find("div", { "id" : "caption" })
        captionTxt = caption.string
        #Kuressaare linnus, vaade põhjast (SM F 3761:473 F); Saaremaa Muuseum; Faili nimi:smf_3761_473.jpg
        (capPart1, museumName, capPart3) = captionTxt.split(';')
        museumName = museumName.strip()
        matchItemRef = re.search("\((.+?)\)", capPart1)
        if (matchItemRef and matchItemRef.group(1)): 
            outImage.source = '[' +  url + ' ' + museumName + ', ' + matchItemRef.group(1) + ']'
            outImage.source.strip()
        matchName = re.search("(.+?)\(.+Faili nimi:(.+?)$", captionTxt)
        if (matchName and matchName.group(1)): 
            outImage.name = matchName.group(1).strip() + ', ' + matchName.group(2)
        #print outImage.url, "\n", captionTxt, "\n", outImage.name, "\n", outImage.source, "\n"

        mainTable = soup.find("table", {"class" : "data highlighted"})
        outDesc = getWikiTable(mainTable)
        
        mainTable = soup.find("table", {"class" : "data"})
        outDesc += getWikiTable(mainTable)

        mainTable = soup.find("table", {"class" : "data full_length"})
        outDesc += getWikiTable(mainTable)
        
        outImage.description = '{{et|1=' + outDesc + '}}'
        outImage.license = '{{PD-old}}'
        
        ##add categories
        if museumData.get(museumName).get('cat'):
            outImage.categories.append( museumData.get(museumName).get('cat') )
        else:
            print "Category not found! \n"

            
    return outImage


def addToGallery(inSite, inPageName, inFiles):

    galleryPage = pywikibot.Page(inSite, inPageName)
    pageTxt = galleryPage.get()
    addTxt = u''

    localtime = time.asctime( time.localtime(time.time()) )
    addTxt += "== " + localtime + " ==\n\n"
    addTxt += "<gallery>\n"
    for fileName in inFiles:
        addTxt += fileName + ' | ' + fileName + "\n"
    addTxt += "</gallery>\n\n"
    commentText = u'Üles laaditud %d pilti' % len(inFiles)
    
    galleryPage.put(pageTxt + "\n" + addTxt, comment = commentText)

def main():

    wikiSite = pywikibot.getSite(u'et', u'wikipedia')
    wikiPageName = u'Kasutaja:KrattBot/Muis.ee-st Commonsisse kopeerimiseks esitatud pildid'
    muisUrls = getMuisUrls(wikiSite, wikiPageName)

    uploadSite = pywikibot.getSite('commons', 'commons')

   
    uploadedFiles = []
    for muisUrl in muisUrls:
        answer = pywikibot.inputChoice(u'Include image %s?'
                                       % muisUrl, ['yes', 'no', 'stop'],
                                       ['y', 'N', 's'], 'N')
        if answer == 'y':
            aImage = getImage(muisUrl)
            while True:
                cat = pywikibot.input(
                    u"Specify a category (or press enter to end adding categories)")
                if not cat.strip(): break
                aImage.categories.append( cat )

            uploadBot = upload.UploadRobot(aImage.url,
                                    description=aImage.getFullDesc(),
                                    useFilename=aImage.name,
                                    keepFilename=True,
                                    verifyDescription=False,
                                    ignoreWarning=False, 
                                    targetSite=uploadSite)
            upFile = uploadBot.run()
            if upFile:
                uploadedFiles.append(upFile)
        elif answer == 's':
            break

    galPageName = u'Kasutaja:KrattBot/Muis.ee-st Commonsisse kopeeritud pildid'  
    if uploadedFiles:
        addToGallery(wikiSite, galPageName, uploadedFiles)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
