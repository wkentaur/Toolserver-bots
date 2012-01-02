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
import StringIO, hashlib, base64

#en names for diffrent museums
museumData = {
    ('Dr.Fr.R.Kreutzwaldi Memoriaalmuuseum') : {
    'enName' : u'Kreutzwald Memorial Museum'
    },
    ('Eesti Kunstimuuseum') : {
    'enName' : u'Art Museum of Estonia'
    },
    ('Eesti Rahva Muuseum') : {
    'enName' : u'Estonian National Museum'
    },
    ('Järvamaa Muuseum') : {
    'enName' : u'Järvamaa Museum'
    },
    ('Palamuse O.Lutsu Kihelkonnakoolimuuseum') : {
    'enName' : u'Palamuse Museum'
    },
    ('Põlva Talurahvamuuseum') : {
    'enName' : u'Põlva Peasant Museum'
    },
    ('Saaremaa Muuseum') : {
    'enName' : u'Saaremaa Museum'
    },
    ('SA Virumaa Muuseumid') : {
    'enName' : u'Virumaa Museums'
    },
    ('Tartu Linnamuuseum') : {
    'enName' : u'Tartu City Museum'
    },
    ('Tartumaa Muuseum') : {
    'enName' : u'Tartu County Museum'
    },
    ('Valga Muuseum') : {
    'enName' : u'Valga Museum'
    }
}

# classes

class Image:
#Constructor with default arguments
   def __init__(self, url = u''):
     self.url = url
     self.artist = u''
     self.title = u''
     self.description = u''
     self.date = u''
     self.medium = u''
     self.dimensions = u''
     self.institution = u''
     self.location = u''
     self.references = u''
     self.object_history = u''
     self.credit_line = u''
     self.inscriptions = u''
     self.notes = u''
     self.accession_number = u''
     self.source = u''
     self.permission = u''
     self.other_versions = u''
     self.license = u''
     self.categories = []
    
   def getFullDesc(self):
    outFDesc = u'=={{int:filedesc}}==\n\
{{Artwork \n\
|artist = %s \n\
|title = %s \n\
|description = %s \n\
|date = %s \n\
|medium = %s \n\
|dimensions = %s \n\
|institution = %s \n\
' % (self.artist, self.title, self.description, self.date, self.medium, self.dimensions, self.institution)
    if self.location:
        outFDesc += '|location = %s \n' % self.location
    if self.references:
        outFDesc += '|references = %s \n' % self.references
    if self.object_history:
        outFDesc += '|object_history = %s \n' % self.object_history
    if self.credit_line:
        outFDesc += '|credit_line = %s \n' % self.credit_line
    if self.inscriptions:
        outFDesc += '|inscriptions = %s \n' % self.inscriptions
    if self.notes:
        outFDesc += '|notes = %s \n' % self.notes
    outFDesc += '|accession_number = %s \n' % self.accession_number
    outFDesc += '|source = %s \n' % self.source
    outFDesc += '|permission = %s \n' % self.permission
    outFDesc += '|other_versions = %s \n' % self.other_versions
    outFDesc += '}} \n\
\n\
=={{int:license-header}}== \n\
%s \n\n' % self.license


    for aCat in self.categories:
        outFDesc += "[[Category:%s]]\n" % (aCat,)
    
    return outFDesc

     
# functions
def downloadPhoto(photoUrl = ''):
    '''
    Download the photo and store it in a StrinIO.StringIO object.

    TODO: Add exception handling

    '''
    imageFile=urllib.urlopen(photoUrl).read()
    return StringIO.StringIO(imageFile)

def findDuplicateImages(photo=None,
                        site=pywikibot.getSite(u'commons', u'commons')):
    ''' Takes the photo, calculates the SHA1 hash and asks the mediawiki api
    for a list of duplicates.

    TODO: Add exception handling, fix site thing

    '''
    hashObject = hashlib.sha1()
    hashObject.update(photo.getvalue())
    return site.getFilesFromAnHash(base64.b16encode(hashObject.digest()))
    
def getMuisUrls(inSite, inPageName):
    outUrls = []
    urlsPage = pywikibot.Page(inSite, inPageName)
    pageTxt = urlsPage.get()
    outUrls = re.findall(r"http://www.muis.ee/portaal/museaalview/\d+", pageTxt)
    
    return outUrls


def getWikiTable(inTable, inImage):
    wikiTable = u''

    if inTable:
        wikiTable = "<table>\n"
        rows = inTable.findAll('tr')
        for row in rows:
            cells = []
            readNumber = False
            readTitle = False
            readMuseumName = False
            colsH = row.findAll('th')
            for col in colsH:
                colText = " ".join(col.findAll(text=True))
                if colText == 'Number':
                    readNumber = True
                elif colText == 'Nimetus':
                    readTitle = True
                elif colText == '' and col.findAll('img'):
                    readMuseumName = True
                else:
                    cells.append( colText )
            cols = row.findAll('td')
            for col in cols:
                colText = " ".join(col.findAll(text=True))
                if readNumber:
                    inImage.accession_number = colText
                elif readTitle:
                    inImage.title = colText
                elif readMuseumName:
                    #do nothing
                    doNothing = ''
                else:
                    cells.append( colText )
            if cells:
                wikiTable += "<tr>\n"
                wikiTable += "<td>\n"            
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
        outDesc = getWikiTable(mainTable, outImage)
        
        mainTable = soup.find("table", {"class" : "data"})
        outDesc += getWikiTable(mainTable, outImage)

        mainTable = soup.find("table", {"class" : "data full_length"})
        outDesc += getWikiTable(mainTable, outImage)
        
        outImage.description = '{{et|1=' + outDesc + '}}'
        outImage.license = '{{PD-old}}'
        
        ##add categories
        if museumData.get(museumName).get('enName'):
            outImage.institution = '{{Institution:' + museumData.get(museumName).get('enName') + '}}'
            museumCat = u'Images from the ' + museumData.get(museumName).get('enName')
            outImage.categories.append( museumCat )
        else:
            print "Museum enName not found in %s! \n" % url
            return None

            
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
    galPageName = u'Kasutaja:KrattBot/Muis.ee-st Commonsisse kopeeritud pildid'  
    muisUrls = getMuisUrls(wikiSite, wikiPageName)

    uploadSite = pywikibot.getSite('commons', 'commons')

   
    uploadedFiles = []
    for muisUrl in muisUrls:
        answer = pywikibot.inputChoice(u'Include image %s?'
                                       % muisUrl, ['yes', 'no', 'stop'],
                                       ['Y', 'n', 's'], 'Y')
        if answer == 'y':
            aImage = getImage(muisUrl)
            if aImage:
                upFile = None
                downloadedImage = downloadPhoto(aImage.url)

                duplicates = findDuplicateImages(downloadedImage)
                if duplicates:
                    pywikibot.output(u'Found duplicate of %s image at %s' % ( muisUrl, duplicates.pop() ) )
                else:            
            
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

    if uploadedFiles:
        addToGallery(wikiSite, galPageName, uploadedFiles)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
