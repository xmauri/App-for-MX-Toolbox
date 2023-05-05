# Table of Contents

-   [Introduction]
-   [Prerequisites]
-   [Architecture]
-   [Installation]
-   [Use Cases]
-   [Upgrade Instructions]
-   [Reference Material]

# Introduction

This README.md file provides documentation for the [App Name] app. This app is designed to [brief description of goals and features of the app].

# Prerequisites

-   [List of any software, hardware, or licensing requirements necessary for the app to function correctly]
-   [Explanation of any technologies or concepts that users need to be familiar with in order to use the app]

# Architecture

[Description of the app's structure, including any components and how they interact with each other] [Include a diagram if helpful]

# Installation

To install the [App Name] app, follow these steps:

1.  [Detailed, sequence-ordered steps for installing the app]
2.  [Any specific commands required for installation]

# Use Cases

[Explanation of how to use the app to achieve the goals stated in the Introduction] [Provide a separate section for each unique use case with detailed instructions]

# Upgrade Instructions

If you are upgrading from a previous version of the [App Name] app, follow these steps:

1.  [Detailed, sequence-ordered steps for upgrading the app]
2.  [Any relevant changes in structure or operation that existing users should expect]

# Reference Material

[List of any lookup tables, saved searches, scripted inputs, or other knowledge objects included in the app, with instructions for use]


# MX Toolbox

*Disclaimer: the app is not affiliated with MX Toolbox. It has been developed independently*

This app has been created by Marco Malagoli with the purpose to satisfy Splunk integration with the MXToolbox service (https://mxtoolbox.com)

## Commands

 - ipqsip built to query API on IP addresses
 - ipqsemail built to query API on email addresses

## Configuration

The API key from MXToolbox should be saved in the Splunk passwords storage, performing:

`curl -k -u admin https://<SPLUNK_INSTANCE>:8089/servicesNS/nobody/TA-moviri_mxtoolbox_command/storage/passwords -d name=<KEY_IDENTIFIER> -d password=<API_KEY>`

You should also configure a cache interval in the mxt_settings.conf file


## Dashboard

This app comes with a **demo** dashboard to test the service.

