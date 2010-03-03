#!/usr/bin/perl
#
# ISBN searching
#

use strict;

use CGI qw/:standard/;
use Template;
use Data::Dumper qw(Dumper);

my $tt = Template->new({
    INCLUDE_PATH => '/home/jhamilto/dev/worthit',
    INTERPOLATE => 1,
});

#print "Content-type: text/html\n\n";
print "Content-type: text/plain\n\n";

print "Creating a query and testing a change...\n";
my %testinput = {"isbns" => "
1881548902
0141304707
0590687336",
};
#my $query = new CGI(%testinput);
my $query = new CGI();

#print "Printing query parameters:\n";
my @isbns = split("\n", $query->param("isbns"));
print "isbns:\n@isbns\n";
#exit(0);

use Net::Amazon;
#use Log::Log4perl qw(:easy);

#Log::Log4perl->easy_init($DEBUG);


sub output_prop($) {
    my ($prop) = (shift);
    
    #print "Generic fields:\n";
    print $prop->ProductName(), "\n";
    print "publication_date: ", $prop->publication_date(), ", publisher: ", $prop->publisher(), ", numpages: ", $prop->numpages(), "\n";
    print "Media:'", $prop->Media(), "', ASIN: ", $prop->ASIN(), ", SalesRank: '", $prop->SalesRank(), "'\n";

    if ($prop->ListPrice()) { print "List: ", $prop->ThirdPartyNewCount(), " from ", $prop->ListPrice(); }
    if ($prop->OurPrice())  { print ", Our: ", $prop->OurPrice(); }
    if ($prop->UsedPrice()) { print ", Used: ", $prop->UsedCount(), " from ", $prop->UsedPrice(); }
    if ($prop->CollectiblePrice()) { print ", Collectible: ", $prop->CollectibleCount(), " from ", $prop->CollectiblePrice(); }
    print "\n";

    #print "List: ", $prop->ListPrice(), " Our: ", $prop->OurPrice(), " Used: ", $prop->UsedPrice(), " Collectible: ", $prop->CollectiblePrice(), "\n";
    
    #for my $pf (@propertyfields) {
    #    print $pf, ":\t", $prop->$pf(), "\n";
    #}
    #print "Book fields:\n";
    #for my $pf (@bookfields) {
    #    print $pf, ":\t", $prop->$pf(), "\n";
    #}
}

sub prop_compare($$) {
    my ($pa, $pb) = (shift, shift);

    my ($sa, $sb) = (20000000, 20000000);
    if (length($pa->SalesRank())) { $sa = int($pa->SalesRank()); }
    if (length($pb->SalesRank())) { $sb = int($pb->SalesRank()); }
    return $sa <=> $sb;
}



my $ACCESS_KEY_ID = $ENV{'AMAZON_ACCESS_KEY'};
my $SECRET_ACCESS_KEY = $ENV{'AMAZON_SECRET_KEY'};


my $ua = Net::Amazon->new(
    token => $ACCESS_KEY_ID,
    secret_key => $SECRET_ACCESS_KEY,
    max_pages => 5);

my $response = $ua->search(asin => \@isbns);


if ($response->is_success()) {
    my @propertyfields = (###"ASIN", "ProductName", 
                          #"Availability", "Catalog",
                          #"ReleaseDate", 
                          #"Manufacturer",
                          ###"ListPrice", "OurPrice", "UsedPrice", "SalesRank",
                          ###"Media", 
                          #"NumMedia", 
                          ###"CollectiblePrice", 
                          "CollectibleCount", "NumberOfOfferings", "UsedCount",
                          "TotalOffers", "ThirdPartyNewPrice", 
                          "ThirdPartyNewCount");
    my @bookfields = ("authors", "publisher", "title", "isbn", "edition", 
                      "ean", "numpages", "dewey_decimal", "publication_date");

    my $i = 0;
    for my $prop ($response->properties) {
        #my $reason = is_valid($query, $prop);
        #print "PROPERTY $i invalid, reason:", $reason, "\n";
        if (0) { #length($reason)) {
            #print "PROPERTY $i invalid, reason:", $reason, "\n";
        } else {
	    print "PROPERTY $i\n";
	    output_prop($prop);

	    if (0) {
            print "PROPERTY $i\n";
            #print "Generic fields:\n";
            print $prop->ProductName(), "\n";
            print "Media:'", $prop->Media(), "', ASIN: ", $prop->ASIN(), ", SalesRank: ", $prop->SalesRank(), "\n";
            print "List: ", $prop->ListPrice(), " Our: ", $prop->OurPrice(), " Used: ", $prop->UsedPrice(), " Collectible: ", $prop->CollectiblePrice(), "\n";
            
            for my $pf (@propertyfields) {
                print $pf, ":\t", $prop->$pf(), "\n";
            }
            print "Book fields:\n";
            for my $pf (@bookfields) {
                print $pf, ":\t", $prop->$pf(), "\n";
            }
	    }
        }
        print "\n\n";
        $i++;
    }
} else {
    print "Error: ", $response->message(), "\n";
}

