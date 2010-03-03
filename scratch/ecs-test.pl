#!/usr/bin/perl

use strict;

my $ACCESS_KEY_ID = $ENV{"AMAZON_ACCESS_KEY"};
my $SECRET_ACCESS_KEY = $ENV{"AMAZON_SECRET_KEY"};

use Net::Amazon;
#use Log::Log4perl qw(:easy);

#Log::Log4perl->easy_init($DEBUG);

my $ua = Net::Amazon->new(
    token => $ACCESS_KEY_ID,
    secret_key => $SECRET_ACCESS_KEY);

my $response = $ua->search(keyword => 'scandal endo', mode => 'books');

if ($response->is_success()) {
    for my $prop ($response->properties) {
	print $prop->as_string(), "\n";
    }
} else {
    print "Error: ", $response->message(), "\n";
}
