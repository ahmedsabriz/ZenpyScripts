# ZenpyScripts

Sample scripts for Zendesk Administrators utilising [Zenpy](https://github.com/facetoe/zenpy) library

## Close Solved Tickets

Usage: python3 close_tickets.py

Recommended for Sandbox only. The script closes all solved tickets. Useful before making changes to users and organizations.

## Help Center Migration

Usage: python3 hc_migration.py

The script copies guide categories, sections, articles, translations, permission groups, and user segments to any destination instance

## Incident Monitoring Report

Usage: python3 incidents_report.py [-h] [-s SUBDOMAIN] [-o OAUTHTOKEN] [-u USERNAME] [-p PASSWORD] [-t APITOKEN] [--start STARTDATE]
[--end ENDDATE]

Sample Zenpy Script to create CSV report of number of incidents per problem ticket. Credentials can be configured in .env file or
overriden through optional arguments.

optional arguments:
-h, --help show this help message and exit
-s SUBDOMAIN Zendesk Subdomain (e.g. d3v-test)
-o OAUTHTOKEN Pre-generated OAuth2 token with "tickets:read write" scope
-u USERNAME Agent Zendesk email address
-p PASSWORD Agent Zendesk password
-t APITOKEN
--start STARTDATE Lower limit of incident ticket creation date (YYYY-MM-DD). Defaults to last week.
--end ENDDATE Upper limit of incident ticket creation date (YYYY-MM-DD). Defaults to today
