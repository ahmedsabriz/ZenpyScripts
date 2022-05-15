# ZenpyScripts © 2022 by @ahmedsabriz is licensed under
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International
# SPDX-License-Identifier: CC-BY-NC-ND-4.0
# https://creativecommons.org/licenses/by-nc-nd/4.0/

import config
import logging
from argparse import ArgumentParser, Namespace
from datetime import datetime, timedelta
from dotenv import load_dotenv
from os import environ
from requests import Session
from zenpy import Zenpy
import csv

logger = logging.getLogger(__name__)


def main():

    # Parsing CLI arguments
    parser = ArgumentParser(
        description="Sample Zenpy Script to create CSV report of number of incidents per problem ticket. Credentials can be configured in .env file or overriden through optional arguments."
    )
    parser.add_argument(
        "-s",
        action="store",
        type=str.lower,
        dest="subdomain",
        help="Zendesk Subdomain (e.g. d3v-test)",
    )
    parser.add_argument(
        "-o",
        action="store",
        type=str.lower,
        dest="oauthtoken",
        help='Pre-generated OAuth2 token with "tickets:read write" scope',
    )
    parser.add_argument(
        "-u",
        action="store",
        type=str.lower,
        dest="username",
        help="Agent Zendesk email address",
    )
    parser.add_argument(
        "-p",
        action="store",
        type=str.lower,
        dest="password",
        help="Agent Zendesk password",
    )
    parser.add_argument(
        "-t",
        action="store",
        dest="apitoken",
        type=str.lower,
    )
    parser.add_argument(
        "--start",
        action="store",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=(datetime.now() - timedelta(days=70)).strftime("%Y-%m-%d"),
        dest="startdate",
        help="Lower limit of incident ticket creation date (YYYY-MM-DD). Defaults to last week.",
    )
    parser.add_argument(
        "--end",
        action="store",
        type=lambda s: datetime.strptime(s, "%Y-%m-%d"),
        default=datetime.now().strftime("%Y-%m-%d"),
        dest="enddate",
        help="Upper limit of incident ticket creation date (YYYY-MM-DD). Defaults to today",
    )

    parser.parse_args(namespace=Namespace)

    load_dotenv()
    creds = {
        "subdomain": Namespace.subdomain
        if Namespace.subdomain
        else environ["SUBDOMAIN"],
        "oauth_token": Namespace.oauthtoken
        if Namespace.oauthtoken
        else environ.get("TICKETS_OAUTH_TOKEN"),
        "email": Namespace.username if Namespace.username else environ.get("EMAIL"),
        "password": Namespace.password
        if Namespace.password
        else environ.get("PASSWORD"),
        "token": Namespace.apitoken if Namespace.apitoken else environ.get("TOKEN"),
    }

    session = Session()
    session.headers["Content-Type"] = "application/json"

    if not creds["oauth_token"]:
        creds.pop("oauth_token")
        if not creds["email"]:
            parser.print_help()
            parser.exit()
        elif not creds["password"]:
            creds.pop("password")
            if not creds["token"]:
                parser.print_help()
                parser.exit()
            else:
                session.auth = (environ["EMAIL"] + "/token", environ["TOKEN"])
        else:
            session.auth = (environ["EMAIL"], environ["TOKEN"])
    else:
        creds.pop("password")
        creds.pop("token")
        session.headers["Authorization"] = "Bearer " + creds["oauth_token"]

    # Start Client
    zenpy_client = Zenpy(**creds, session=session)

    number_of_incidents = {"NULL": 0}
    for ticket in zenpy_client.search(
        type="ticket",
        created_between=[Namespace.startdate, Namespace.enddate],
        ticket_type="incident",
        sort_by="created_at",
        sort_order="asc",
    ):
        if not ticket.problem_id:
            number_of_incidents["NULL"] += 1
        else:
            try:
                number_of_incidents[ticket.problem_id] += 1
            except:
                number_of_incidents[ticket.problem_id] = 1

    rows = []
    for problem in number_of_incidents.items():
        if problem[0] != "NULL":
            rows.append(
                [problem[0], zenpy_client.tickets(id=problem[0]).subject, problem[1]]
            )
    rows.append(["NULL", "NULL", number_of_incidents["NULL"]])

    with open("./incidents_report.csv", "w", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Problem ID", "Subject", "Number of Incidents"])
        writer.writerows(rows)


if __name__ == "__main__":
    main()
