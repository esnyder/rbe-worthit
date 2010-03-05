#!/usr/bin/env python
#

import os, sys, re, lxml, cgi, cgitb, unicodedata, locale, time
import StringIO
from ConfigParser import *
from amazonproduct import *

cgitb.enable()


def dosearch(api, isbn, page):
    node = None
    try:
        node = api.item_lookup(isbn, IdType="ISBN", SearchIndex="All", MerchantId="All", Condition="All", ResponseGroup="Medium,Offers", OfferPage=page)
    except InvalidParameterValue, e:
        if e.args[0] == "ItemId":
            pass
        else:
            raise e
    return node

def safe_note(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')

# do it this way so we can get two or more pages of offers right off the bat
def collectlowprices(bycond, item):
    if item is None:
        return

    try:
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


def firstof(lxmlnode, possibleattributes, default="(none)"):
    for attr in possibleattributes:
        try:
            res = lxmlnode.__getattr__(attr)
            return res
        except AttributeError, e:
            pass
    return default


def formatitem(item, item2):
    res = StringIO.StringIO()
    try:
        atr = item.ItemAttributes

        print >>res, "<td>"
        author = firstof(atr, ["Author", "Artist", "Creator"])
        pub = firstof(atr, ["Publisher", "Label"])
        sr = firstof(item, ["SalesRank"], 0)
        print >>res, atr.Title, "<br>ASIN: ", item.ASIN, "<br>by", author, ",", pub, "sales rank:", locale.format("%d", int(sr), True)
        print >> res, "</td>"

        offs = item.OfferSummary
        print >>res, "<td>"
        try:
            print >>res, "%d New from %s<br>" % (offs.TotalNew, offs.LowestNewPrice.FormattedPrice)
        except:
            print >>res, "0 New available<br>"
        try:
            print >>res, "%d Used from %s<br>" % (offs.TotalUsed, offs.LowestUsedPrice.FormattedPrice)
        except:
            print >>res, "0 Used available</br>"
        try:
            print >>res, "%d Collectible from %s<br>" % (offs.TotalCollectible, offs.LowestCollectiblePrice.FormattedPrice)
        except:
            print >>res, "0 Collectible available</br>"
        print >>res, "</td>"

        bycond = dict()
        collectlowprices(bycond, item)
        collectlowprices(bycond, item2)

        print >>res, "<td>"
        for key in bycond.keys():
            print >>res, "%s: %s" % (key, ' '.join(bycond[key]))
            print >>res, "<br>"
        print >>res, "</td>"
        
        print >>res, "</tr>"

        # debugging, dump the item into the table too
        #print >>res, "<tr><td colspan=3>", str(item).replace("\n", "<br>"), "</td></tr>"
    except:
        res.truncate(0)
        print >>res, "<tr><td colspan=3>Unknown exception: ", str(sys.exc_type), str(sys.exc_value), str(sys.exc_traceback), "</td></tr>"
    return res.getvalue()


def process_isbns(isbns):
    print "<table border='1'>"
    print "<tr><th>Item Details</th><th>Offer Summary</th><th>20 Lowest Priced Offers</th></tr>"

    for isbn in isbns:
        node = dosearch(api, isbn, 1)

        if node is None:
            print "<tr><td colspan=3><b>INVALID ISBN: ", isbn, "</b></td></tr>"
        else:
            item2 = None
            if node.Items.Item.Offers.TotalOffers > 10:
                node2 = dosearch(api, isbn, 2)
                if node2 is not None: item2 = node2.Items.Item
            print formatitem(node.Items.Item, item2)

        sys.stdout.flush()
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
    process_isbns(isbns)
else:
    pass

print "<h3>Enter ISBNs (or UPC from CD/DVD/etc.) 1 per line</h3>"

print "<form method='GET'>"
print "<textarea width='80%' name=isbns rows=20></textarea>"
print "<input type='submit' value='Search'/>"
print "</form>"

print "</body></html>"
