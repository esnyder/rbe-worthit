#!/usr/bin/perl

use strict;

my $ACCESS_KEY_ID = $ENV{"AMAZON_ACCESS_KEY"};
my $SECRET_ACCESS_KEY = $ENV{"AMAZON_SECRET_KEY"};

print "my access key: $ACCESS_KEY_ID\n";
print "my secret key: $SECRET_ACCESS_KEY\n";

use Net::Amazon;
use Log::Log4perl qw(:easy);

Log::Log4perl->easy_init($DEBUG);

my $ua = Net::Amazon->new(
    token => $ACCESS_KEY_ID,
    secret_key => $SECRET_ACCESS_KEY);

#my $response = $ua->search(keyword => 'mr. popper\'s penguins atwater', mode => 'books');
my $response = $ua->search(power => "title:mr.+popper's+penguins author:atwater publisher:little|weekly", mode => 'books');

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
        print "\n\n";
        $i++;
    }
} else {
    print "Error: ", $response->message(), "\n";
}
