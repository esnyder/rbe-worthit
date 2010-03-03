#!/usr/bin/perl

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
my $query = new CGI();
my %testinput = {"title" => "the price of victory",
		 "author" => "robert lynn asprin",
		 "publisher" => "guild america books",
		 "media" => "hardcover",
		 "year" => "1989"};
#my $query = new CGI(%testinput);

#print "Printing query parameters:\n";
my ($title, $author, $publisher, $media, $year) = ($query->param("title"),
						   $query->param("author"),
						   $query->param("publisher"),
						   $query->param("media"),
						   $query->param("year"));

$title =~ s/ /+/g;
$author =~ s/ /+/g;
$publisher =~ s/ /+/g;
$media =~ s/ /+/g;
#print $title, "\n";
#print $author, "\n";
#print $publisher, "\n";
#print $media, "\n";
#print $year, "\n";

#exit(0);

my $vars = {title => $title,
	    author => $author,
	    publisher => $publisher,
	    media => $media,
};


use Net::Amazon;
#use Log::Log4perl qw(:easy);

#Log::Log4perl->easy_init($DEBUG);

sub build_power_query($$$) {
    my ($t, $a, $p) = (shift, shift, shift);
    my $q = "title:$t author:$a";
    if (length($p)) {
        $q .= " publisher:$p";
    }
    #print "built power query: '$q'\n";
    return $q;
}

sub is_valid($$) {
    #print "is_valid entered\n";
    my ($query, $prop) = (shift, shift);

    # right format?
    my $m = $prop->Media();
    #print "media is $m\n";
    if (length($m)) {
        if ($m != $query->param('media')) {
            #print "found media mismatch\n";
            return ("media mismatch: $m");
        }
        #print "right kind of media\n";
    }

    # right year?
    my $y = $prop->publication_date();
    #print "year is $y\n";
    if ($y =~ m/(\d{4})(-\d{2}-\d{2})?/) {
        $y = $1;
    }
    #print "year is now $y\n";
    if (length($y)) {
        if (0) { #$y != $query->param("year")) {
            #print "found year mismatch\n";
            return ("year mismatch: $y");
        }
    }

    # has no isbn?
    #print "checking isbn\n";
    if (length($prop->isbn())) {
        #return ("has an isbn");
    }

    # right publisher?

    return "";
}

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
    secret_key => $SECRET_ACCESS_KEY);

my $response = $ua->search(keyword => 'doctor dolittle in the moon', mode => 'books');
#my $response = $ua->search(power => "title:$title author:$author publisher:$publisher", mode => 'books');
#my $response = $ua->search(power => build_power_query($title, $author, $publisher), mode => 'books');

if (1) {

#    print Dumper($response);

if ($response->is_success()) {
    #${$vars}{"propcount"} = length($response->properties);
    #${$vars}{"properties"} = [];
    #for my $prop ($response->properties) {
    #    push_back(${$vars}{"properties"}, $prop);
    #}
    #${$vars}{"properties"} = $response->properties;
    print "printing Data::Dumper representation of the amazon search:\n";
    #print Dumper($response);
    #my $properties = [];
    my $counter = 1;
    for my $prop ($response->properties) {
	print "PROPERTY $counter:\n";
	print Dumper($prop);
	#push_back($properties, $prop);
	$counter+=1;
    }
    #${$vars}{"properties"} = $properties;
    print "now the template stuff\n";
    print "\n\n------------------------------------------------------------------\n\n\n";
    $tt->process("noisbnsearch.tmpl", $vars);
} else {
    print "Error: ", $response->message(), "\n";
}
#exit(0);
} else {

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
    for my $prop (sort prop_compare $response->properties) {
        my $reason = is_valid($query, $prop);
        #print "PROPERTY $i invalid, reason:", $reason, "\n";
        if (length($reason)) {
            print "PROPERTY $i invalid, reason:", $reason, "\n";
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

}
