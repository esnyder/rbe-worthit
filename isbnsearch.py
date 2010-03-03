#!/usr/bin/env python
#

import os, sys, re, lxml, cgi, cgitb, unicodedata
from ConfigParser import *
from amazonproduct import *

cgitb.enable()


def dosearch(isbnstring, page):
    # api = API(os.getenv("AMAZON_ACCESS_KEY"), os.getenv("AMAZON_SECRET_KEY"), "us")
    cfg = ConfigParser()
    cfg.read("/etc/apache2/amazon.keys")
    api = API(cfg.get("keys", "AMAZON_ACCESS_KEY"), cfg.get("keys", "AMAZON_SECRET_KEY"), "us")
    
    node = api.item_lookup(isbnstring, IdType="ISBN", SearchIndex="Books", MerchantId="All", Condition="All", ResponseGroup="Medium,Offers", OfferPage=page)
    lxml.objectify.enable_recursive_str(True)
    
    return node

def safe_note(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

# do it this way so we can get two or more pages of offers right off the bat
def collectlowprices(bycond, isbn, node):
    try:
        for item in node.Items.Item:
            if isbn == item.ItemAttributes.ISBN:
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
    except AttributeError as e:
        pass

def outputsearch(node, node2):
    print "<table border='1'>"
    
    print "<tr><th>Item Details</th><th>Offer Summary</th><th>20 Lowest Priced Offers</th></tr>"
    
    for item in node.Items.Item:
        print "<tr>"
        atr = item.ItemAttributes
        print "<td>"
        print atr.Title, "<br>", atr.ISBN, "<br>by", atr.Author, ",", atr.Publisher, "sales rank:", item.SalesRank
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
        collectlowprices(bycond, atr.ISBN, node)
        collectlowprices(bycond, atr.ISBN, node2)

        print "<td>"
        for key in bycond.keys():
            print "%s: %s" % (key, ' '.join(bycond[key]))
            print "<br>"
        print "</td>"
        print "</tr>"
    print "</table>"


print "Content-Type: text/html\n\n"

print "<html><head></head>\n<body>"

isbnstring = ""
form = cgi.FieldStorage()

if form.has_key("isbns"):
    isbnstring = ', '.join(form["isbns"].value.split())
if isbnstring == "":
    #isbnstring = "0486247791, 0141304707"
    pass
else:
    node = dosearch(isbnstring, 1)
    node2 = dosearch(isbnstring, 2)
    outputsearch(node, node2)

print "<h3>Enter ISBNs 1 per line</h3>"

print "<p>Sorry, books only right now, no DVD/CD/etc."

print "<form method='GET'>"
print "<textarea width='80%' name=isbns rows=20></textarea>"
print "<input type='submit' value='Search'/>"
print "</form>"

print "</body></html>"
