## Introduction

This app is designed to integrating MX Toolbox feature with Splunk.

## Prerequisites

-   Python

## Installation

To install the MX-Toolbox app just unpack and deploy to the Splunk SH instance.

## Reference Material

 - https://docs.splunk.com/Documentation/SCS/current/SearchReference/CustomCommandFunctions


## MX Toolbox

*Disclaimer: the app is not affiliated with MX Toolbox. It has been developed independently*

This app has been created by Marco Malagoli with the purpose to satisfy Splunk integration with the MXToolbox service (https://mxtoolbox.com)

## Commands

 - mx domain_field action=mx. Get DNS MX records for the specified domain field.
 - mx ip_field action=blacklist. Check IP or host for reputation.
 - mx domain_field action=dns. Check your DNS Servers for possible problems.

## Configuration

The API key from MXToolbox should be saved in the Splunk passwords storage, performing:

`curl -k -u admin https://<SPLUNK_INSTANCE>:8089/servicesNS/nobody/<app_name>/storage/passwords -d name=<KEY_IDENTIFIER> -d password=<API_KEY>`

You should also configure a cache interval in the mxt_settings.conf file


## Dashboard

This app comes with a **demo** dashboard to test the service.

