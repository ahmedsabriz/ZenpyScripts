# ZenpyScripts © 2022 by @ahmedsabriz is licensed under
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International
# SPDX-License-Identifier: CC-BY-NC-ND-4.0
# https://creativecommons.org/licenses/by-nc-nd/4.0/

# Sample Script to close all solved tickets

from zenpy import Zenpy
from dotenv import load_dotenv
from os import environ

load_dotenv()

creds = {
    "email": environ["EMAIL"],
    "token": environ["TOKEN"],
    "subdomain": environ["SUBDOMAIN"],
}

# Start Client
zenpy_client = Zenpy(**creds)

for ticket in zenpy_client.search(type="ticket", status="solved"):
    ticket.status = "closed"
    zenpy_client.tickets.update(ticket)
