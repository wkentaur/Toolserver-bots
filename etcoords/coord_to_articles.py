#!/usr/bin/python
# -*- coding: utf-8  -*-
'''

add article coordinates (Coordinate template) to et.wiki articles
from coordinates database

Usage: python coord_to_articles.py -sourcewiki:XX

'''

import sys, os
sys.path.append("/home/kentaur/py/pywikipedia")
import wikipedia
import re, MySQLdb, time
import logging



# "constants"

# wikipedia article namespace
WP_ARTICLE_NS = 0
# wikipedia category namespace
WP_CATEGORY_NS = 14
# output debug messages
DEBUG = True


     
     
# functions


def connectWikiDatabase(lang):
    '''
    Connect to the wiki database
    '''
    if (lang):
        hostName = lang + 'wiki-p.db.toolserver.org'
        dbName = lang + 'wiki_p'
        #coordDbName = 'u_dispenser_p'
        conn = MySQLdb.connect(host=hostName, db=dbName,
            read_default_file=os.path.expanduser("~/.my.cnf"), 
            use_unicode=True, charset='utf8')
        cursor = conn.cursor()
        return (conn, cursor)



def getPageIdWithoutCoord( pageName, conn, cursor, lang ):
    '''
    get Wikipedia pagename pageId for page without coordinates
    '''
    
    pageNamespace = WP_ARTICLE_NS
    followRedirect = False
    #underscores   
    pageName = pageName.replace(u' ', u'_')
    retStatus = ''
    pageId = ''
    redirNs = ''
    redirTitle = u''
    coordTable = "u_dispenser_p.coord_" + lang + "wiki"

    
    query = """SELECT page_id, page_is_redirect FROM page 
        LEFT JOIN """ + coordTable + """ ON gc_from = page_id
        WHERE page_namespace = %s AND page_title = %s
        AND gc_from IS NULL"""
    cursor.execute(query, (pageNamespace, pageName))
    if DEBUG:
        print cursor._executed
        print u'rowcount: %d ' % cursor.rowcount

    if (cursor.rowcount > 0):
        row = cursor.fetchone()
        (pageId, IsRedirect) = row
        if (IsRedirect):
            if (followRedirect):
                (redirNs, redirTitle) = getRedirPageNsTitle(pageId, cursor)
                redirTitle = unicode(redirTitle, "utf-8")
                (dummy0, pageId, dummy1, dummy2) = getPageId(redirTitle, conn, cursor, redirNs)
                retStatus = 'FOLLOWED_REDIR'
            else:
                retStatus = 'REDIRECT'
        else:
            retStatus = 'OK'
    
    return (retStatus, pageId, redirNs, redirTitle)

def getRedirPageNsTitle(pageId, cursor):
    '''
    Get redirect page namespace and title.
    '''

    if (pageId):
        pageNs = ''
        pageTitle = u''
    
        query = """SELECT rd_namespace, rd_title FROM redirect
                WHERE rd_from = %s"""
        cursor.execute(query, (pageId,))

        if (cursor.rowcount > 0):
            row = cursor.fetchone()
            (pageNs, pageTitle) = row
    
        return (pageNs, pageTitle)
    
    
def addCoords(sourceWiki, lang, article, lat, lon, region, type, dim):
    '''
    Add the coordinates to article.
    '''

    if (article and lang and type):
        coordTemplate = 'Coordinate'
        site = wikipedia.getSite(lang, 'wikipedia')

        page = wikipedia.Page(site, article)
        try:
            text = page.get()
        except wikipedia.NoPage: # First except, prevent empty pages
            logging.warning('Page empty: %s', article)
            return False
        except wikipedia.IsRedirectPage: # second except, prevent redirect
            logging.warning('Page is redirect: %s', article)
            wikipedia.output(u'%s is a redirect!' % article)
            return False
        except wikipedia.Error: # third exception, take the problem and print
            logging.warning('Some error: %s', article)
            wikipedia.output(u"Some error, skipping..")
            return False       
    
        if coordTemplate in page.templates():
            logging.info('Already has Coordinate template: %s', article)
            return False

        if 'Linn' in page.templates():
            logging.info('Linn template without coords: %s', article)
            return False
            
        newtext = text
        replCount = 1
        coordText = u'{{Coordinate |NS=%s |EW=%s |type=%s |region=%s' % (lat, lon, type, region)
        if (dim):
            coordText += u' |dim=%s' % ( int(dim),)
        coordText += '}}'
        localCatName = wikipedia.getSite().namespace(WP_CATEGORY_NS)
        catStart = r'\[\[(' + localCatName + '|Category):'
        catStartPlain = u'[[' + localCatName + ':'
        replacementText = u''
        replacementText = coordText + '\n\n' + catStartPlain
    
        # insert coordinate template before categories
        newtext = re.sub(catStart, replacementText, newtext, replCount, flags=re.IGNORECASE)

        if text != newtext:
            logging.info('Adding coords to: %s', article)
            comment = u'lisan artikli koordinaadid %s.wikist' % (sourceWiki)
            wikipedia.showDiff(text, newtext)
            #modPage = wikipedia.input(u'Modify page: %s ([y]/n) ?' % (article) )
            #if (modPage.lower == 'y' or modPage == ''):
            page.put(newtext, comment)
            return True
        else:
            logging.info('Nothing to change: %s', article)
            return False
    else:
        return False
    
def main():

    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename='log_coord.log',
                    filemode='w')

    sourceWiki = ""
    for arg in wikipedia.handleArgs():
        if arg.startswith('-sourcewiki:'):
            sourceWiki = arg [len('-sourcewiki:'):]

    if (not sourceWiki):
        sys.exit("Source wiki not set at command line with -sourcewiki:XX")
    
    targetWiki = "et"
    coordTable = "u_dispenser_p.coord_" + sourceWiki + "wiki"
    (connSource, cursorSource) = connectWikiDatabase(sourceWiki)
    (connTarget, cursorTarget) = connectWikiDatabase(targetWiki)
    query = """SELECT gc_lat, gc_lon, gc_region, gc_type, gc_dim, ll_title 
    FROM page
    JOIN """ + coordTable + """ ON gc_from = page_id 
    JOIN langlinks ON ll_from = page_id 
    WHERE page_namespace=0 
    AND gc_globe = 'Earth'
    AND gc_primary = 1 
    AND ll_lang = %s"""
    cursorSource.execute(query, (targetWiki,))
    while True:
        try:
            row = cursorSource.fetchone()
            (lat, lon, region, type, dim, targetTitle) = row
            targetTitle = unicode(targetTitle, "utf-8")
            (retStatus, pageId, dummy1, dummy2) = getPageIdWithoutCoord( targetTitle, connTarget, cursorTarget, targetWiki )
            if (pageId):
                addCoords(sourceWiki, targetWiki, targetTitle, lat, lon, region, type, dim)
            else :
                logging.info('Page not found/already has coords from et.wiki: %s', targetTitle)
        except TypeError:
            break   


if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
