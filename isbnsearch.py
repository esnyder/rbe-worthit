#!/usr/bin/env python
#

import os, sys, re, lxml, cgi, cgitb, unicodedata, locale
from ConfigParser import *
from amazonproduct import *

cgitb.enable()


def dosearch(api, isbns, invalidisbns, page):
    node = None
    doagain = True
    while (doagain):
        doagain = False
        isbnstring = ",".join(isbns)
        try:
            node = api.item_lookup(isbnstring, IdType="ISBN", SearchIndex="All", MerchantId="All", Condition="All", ResponseGroup="Medium,Offers", OfferPage=page)
        except InvalidParameterValue, e:
            #print "<p>InvalidParameterValue: %s" % str(e)
            #print "<p>type(e.args): ", type(e.args)
            #print "<p>dir(e): ", dir(e)
            #print "<p>e.args: ", e.args
            if e.args[0] == "ItemId":
                invalidisbns[e.args[1]] = True
                isbns.remove(e.args[1])
                doagain = True
            else:
                raise e
    return node

def safe_note(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

# do it this way so we can get two or more pages of offers right off the bat
def collectlowprices(bycond, isbn, node):
    try:
        for item in node.Items.Item:
            if isbn == item.ASIN:
                for offer in item.Offers.Offer:
                    key = "%s %s" % (offer.OfferAttributes.Condition, offer.OfferAttributes.SubCondition)
                    if not bycond.has_key(key):
                        bycond[key] = list()
                    stars = 0
                    ratings = 0
                    condnote = "(none)"
                    try: 
                        stars = offer.Merchant.AverageFeedbackRating
                        ratings = offer.Merchant.TotalFeedback
                        condnote = safe_note(u'%s' % offer.OfferAttributes.ConditionNote)
                    except: 
                        pass
                    bycond[key].append("<span title='Merchant: %0.1f stars on %d ratings ConditionNote: %s'>" % (stars, ratings, condnote) + str(offer.OfferListing.Price.FormattedPrice) + "</span>")
    except AttributeError, e:
        pass


def firstof(lxmlnode, possibleattributes):
    for attr in possibleattributes:
        try:
            res = lxmlnode.__getattr__(attr)
            return res
        except AttributeError, e:
            pass
    return "(none)"


def outputsearch(node, node2):
    print "<table border='1'>"
    
    print "<tr><th>Item Details</th><th>Offer Summary</th><th>20 Lowest Priced Offers</th></tr>"
    
    for item in node.Items.Item:
        print "<tr>"
        atr = item.ItemAttributes

        print "<td>"
        author = firstof(atr, ["Author", "Artist", "Creator"])
        pub = firstof(atr, ["Publisher", "Label"])
        print atr.Title, "<br>ASIN: ", item.ASIN, "<br>by", author, ",", pub, "sales rank:", locale.format("%d", int(item.SalesRank), True)
        print "</td>"
        
        offs = item.OfferSummary
        print "<td>"
        try:
            print "%d New from %s<br>" % (offs.TotalNew, offs.LowestNewPrice.FormattedPrice)
        except:
            print "0 New available<br>"
        try:
            print "%d Used from %s<br>" % (offs.TotalUsed, offs.LowestUsedPrice.FormattedPrice)
        except:
            print "0 Used available</br>"
        try:
            print "%d Collectible from %s<br>" % (offs.TotalCollectible, offs.LowestCollectiblePrice.FormattedPrice)
        except:
            print "0 Collectible available</br>"
        print "</td>"
        
        bycond = dict()
        collectlowprices(bycond, item.ASIN, node)
        collectlowprices(bycond, item.ASIN, node2)

        print "<td>"
        for key in bycond.keys():
            print "%s: %s" % (key, ' '.join(bycond[key]))
            print "<br>"
        print "</td>"
        print "</tr>"
    print "</table>"


# api = API(os.getenv("AMAZON_ACCESS_KEY"), os.getenv("AMAZON_SECRET_KEY"), "us")
def make_apiobj():
    cfg = ConfigParser()
    cfg.read("/etc/apache2/amazon.keys")
    return API(cfg.get("keys", "AMAZON_ACCESS_KEY"), cfg.get("keys", "AMAZON_SECRET_KEY"), "us")


print "Content-Type: text/html\n\n"

print "<html><head></head>\n<body>"

isbnstring = ""
form = cgi.FieldStorage()

api = make_apiobj()
lxml.objectify.enable_recursive_str(True)

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

isbns = list()
invalidisbns = dict()
if form.has_key("isbns"):
    isbns = form["isbns"].value.split()
    node = dosearch(api, isbns, invalidisbns, 1)
    node2 = dosearch(api, isbns, invalidisbns, 2)
    for i in invalidisbns.keys():
        print "<p><b>INVALID ISBN: ", i, "</b>"
    outputsearch(node, node2)
else:
    pass

print "<h3>Enter ISBNs (or UPC from CD/DVD/etc.) 1 per line</h3>"

print "<form method='GET'>"
print "<textarea width='80%' name=isbns rows=20></textarea>"
print "<input type='submit' value='Search'/>"
print "</form>"

print "</body></html>"
