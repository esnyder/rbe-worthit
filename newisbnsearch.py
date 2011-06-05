#!/usr/bin/env python
#

import os, sys, re, lxml, cgi, unicodedata, locale, time
import cgitb
import StringIO
from ConfigParser import *
from amazonproduct import *
import urllib2 # for exception handling on timeouts from amazonproduct calls
from datetime import date

cgitb.enable()
import shelve

dat = shelve.open("newisbnsearch.dat", writeback=True)
datkey = str(date.fromtimestamp(time.time()).toordinal())
if not dat.has_key(datkey):
    dat[datkey] = {'selected': 0, 'unknown': 0, 'rejected': 0}

def dosearch(api, isbn, page):
    node = None
    try:
        idType = "ISBN"
        if len(isbn) == 12: idType = "UPC"
        node = api.item_lookup(isbn, IdType=idType, SearchIndex="All", MerchantId="All", Condition="All", ResponseGroup="Medium,Offers", OfferPage=page)
    except InvalidParameterValue, e:
        if e.args[0] == "ItemId":
            pass
        else:
            raise e
    return node

def safe_note(s):
    res = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    res = cgi.escape(res, True)
    return res.replace('\'', "&rsquot;")

# do it this way so we can get two or more pages of offers right off the bat
def collectlowprices(bycond, values, item):
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
            if re.match("acceptable", str(offer.OfferAttributes.SubCondition), re.IGNORECASE) is None:
                values.append(int(offer.OfferListing.Price.Amount))
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


#
# rejected, selected or unknown
#
def classifyvalues(values):
    if (values[0] > 300):
        return "selected"
    if (len(values) > 5 and values[4] < 300):
        return "rejected"
    return "unknown"

def formatitem(item, item2):
    res = StringIO.StringIO()
    try:
        atr = item.ItemAttributes
        author = firstof(atr, ["Author", "Artist", "Creator"])
        pub = firstof(atr, ["Publisher", "Label"])
        sr = firstof(item, ["SalesRank"], 0)

        bycond = dict()
        values = list()
        collectlowprices(bycond, values, item)
        collectlowprices(bycond, values, item2)
        values.sort()
        rowclass = classifyvalues(values)
        if dat[datkey].has_key(rowclass):
            dat[datkey][rowclass] += 1
        else:
            dat[datkey][rowclass] = 1

        print >>res, "<tr class='%s'>" % rowclass

        print >>res, "<td>"
        print >>res, "<b>", cgi.escape(str(atr.Title), True), "</b><br>ASIN: ", item.ASIN, "<br>by", cgi.escape(str(author)), ",", cgi.escape(str(pub))
        print >> res, "</td>"

        offs = item.OfferSummary
        print >>res, "<td><table>"
        print >>res, "<tr><td colspan=2>SalesRank <b>", locale.format("%d", int(sr), True), "</b></td></tr>"
        try:
            print >>res, "<tr><td align=right>%d N</td><td> &gt;= %s</td></tr>" % (offs.TotalNew, offs.LowestNewPrice.FormattedPrice)
        except:
            print >>res, "<tr><td align=right>0 N</td><td></td></tr>"
        try:
            print >>res, "<tr><td align=right>%d U</td><td> &gt;= %s</td></tr>" % (offs.TotalUsed, offs.LowestUsedPrice.FormattedPrice)
        except:
            print >>res, "<tr><td align=right>0 U</td><td></td></tr>"
        try:
            print >>res, "<tr><td align=right>%d C</td><td> &gt;= %s</td></tr>" % (offs.TotalCollectible, offs.LowestCollectiblePrice.FormattedPrice)
        except:
            print >>res, "<tr><td align=right>0 C</td><td></td></tr>"
        print >>res, "</table></td>"

        print >>res, "<td><table>"
        for key in bycond.keys():
            print >>res, "<tr><td align=right>%s</td><td>%s</td></tr>" % (key, ' '.join(bycond[key]))
            #print >>res, "<br>"
        print >>res, "</table></td>"
        
        print >>res, "</tr>"

        # debugging, dump the item into the table too
        #print >>res, "<tr><td colspan=3>", str(item).replace("\n", "<br>"), "</td></tr>"
    except:
        res.truncate(0)
        print >>res, "<tr><td colspan=3>Unknown exception: ", str(sys.exc_type), str(sys.exc_value), str(sys.exc_traceback), "</td></tr>"
    return res.getvalue()


def process_isbns(isbns):
    results = dict()
    for i in isbns:
        results[i] = [None, None]

    low = 0
    count = 10
    idType = "ISBN"
    page = 1

    while len(isbns[low:low+count]):
        node = api.item_lookup(",".join(isbns[low:low+count]), IdType=idType, SearchIndex="All", MerchantId="All", Condition="All", ResponseGroup="Medium,Offers", OfferPage=page)
        low += count
        for i in node.Items.Item:
            try:
                itemISBN = i.ItemAttributes.ISBN
                if isbns.__contains__(itemISBN): results[itemISBN][0] = i
            except Exception as e:
                # How to show this?
                pass

    low = 0
    page = 2
    while len(isbns[low:low+count]):
        node = api.item_lookup(",".join(isbns[low:low+count]), IdType=idType, SearchIndex="All", MerchantId="All", Condition="All", ResponseGroup="Medium,Offers", OfferPage=page)
        low += count
        for i in node.Items.Item:
            try:
                itemISBN = i.ItemAttributes.ISBN
                if isbns.__contains__(itemISBN): results[itemISBN][1] = i
            except Exception as e:
                # How to show this?
                pass

    return results

def output_results_for_web(results):
    print "<table border='1'>"
    print "<tr><th>Item Details</th><th>Offer Summary</th><th>20 Lowest Priced Offers</th></tr>"

    for isbn in isbns:
        if results[isbn][0] is None:
            print "<tr><td colspan=3 bgcolor=yellow><b>INVALID ISBN: ", isbn, "</b></td></tr>"
            sys.stdout.flush()
            continue

        item = results[isbn][0]
        item2 = results[isbn][1]

        print formatitem(item, item2)
        sys.stdout.flush()
    print "</table>"


# api = API(os.getenv("AMAZON_ACCESS_KEY"), os.getenv("AMAZON_SECRET_KEY"), "us")
def make_apiobj():
    cfg = ConfigParser()
    cfg.read("/etc/apache2/amazon.keys")
    return API(cfg.get("keys", "AMAZON_ACCESS_KEY"), cfg.get("keys", "AMAZON_SECRET_KEY"), "us")


def display_searches(shelf, key):
    print "<h3>ISBN searches: last 7 days</h3>"
    print "<table border=1>"
    datkeyordinal = int(key)
    print "<tr><th>date</th><th>(sell, ?, shelve)</th><th>total # isbn searches</th></tr>"
    for o in range(datkeyordinal-6, datkeyordinal+1):
        d = str(date.fromordinal(o))
        v = shelf.get(str(o), dict())
        (acc, unkn, rej) = (v.get('selected', 0), v.get('unknown', 0), v.get('rejected', 0))
        print "<tr><td><b>%s</b>: </td><td>(%d, %d, %d)</td><td><b> %d</b></td></tr>" % (d, acc, unkn, rej, acc+unkn+rej)
    print "</table>"

isbnstring = ""
form = cgi.FieldStorage()

api = make_apiobj()
lxml.objectify.enable_recursive_str(True)

locale.setlocale(locale.LC_ALL, 'en_US.utf8')

if __name__ != "main":
    print "Content-Type: text/html\n\n"
    print "<html><head>"
    print "<style type='text/css'>"
    print " .rejected { background-color: #FF0000; }"
    print " .selected { background-color: #00FF00; }"
    print "</style>"
    print "</head>\n<body>"

    isbns = list()
    invalidisbns = dict()
    if form.has_key("isbns"):
        isbns = form["isbns"].value.split()
        results = process_isbns(isbns)
        output_results_for_web(results)
    else:
        pass

    display_searches(dat, datkey)
    #print "ISBN lookups today: ", dat[datkey], "\n"

    dat.close()

    print "<h3>Enter ISBNs (or UPC from CD/DVD/etc.) 1 per line</h3>"

    print "<form method='GET'>"
    print "<textarea width='80%' name=isbns rows=20></textarea>"
    print "<input type='submit' value='Search'/>"
    print "</form>"

    print "</body></html>"
