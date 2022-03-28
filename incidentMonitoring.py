# zendeskIncidentMonitoring © 2022 by @ahmedsabriz is licensed under
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International
# SPDX-License-Identifier: CC-BY-NC-ND-4.0
# https://creativecommons.org/licenses/by-nc-nd/4.0/

from dotenv import load_dotenv
import logging, config
from os import environ
from zenpy import Zenpy
from zenpy.lib.api_objects import Macro, Ticket, Comment, Trigger, View
import requests
from sqlalchemy import null

import json


load_dotenv()

logger = logging.getLogger(__name__)

creds = {
    "email": environ["EMAIL"],
    "token": environ["TOKEN"],
    "subdomain": environ["SUBDOMAIN"],
}
tickets_token = environ["TICKETS_OAUTH_TOKEN"]


def main():
    # TODO: Modify the following sample values
    # Utilities
    tickets_webhook = None
    incident_monitoring_view = None

    # Incident information
    incident_summary = "Profile Outage"
    incident_description = "Due to a technical error, customers have not been able to access their profile since yesterday evening. The error differs depending on the device system"
    incident_tag = "outage_10march"

    # OS tags
    custom_tags = {"os1_tag": "os1", "os2_tag": "os2"}

    # Email body
    macro_html = (
        '<p>Hi {{ticket.requester.first_name}}​,</p> \
                    <!-- Sample Text --> \
                    <p><br>Thank you for reaching out to us. We are aware of a technical issue preventing some of our users from accessing their profile.</p> \
                    <!-- Error details based on os tag --> \
                    {% assign tags = ticket.tags | split: " " %} \
                    {% for tag in tags %} \
                    {% if tag == "'
        + custom_tags["os1_tag"]
        + '" %} \
                    <ul> \
                    <li>We identified Error1 on os1. Here is a workaround or additional details about it.</li> \
                    </ul> \
                    {% endif %} \
                    {% if tag == "'
        + custom_tags["os2_tag"]
        + '" %} \
                    <ul> \
                    <li>We identified Error2 on os2. Here is a workaround or additional details about it.</li> \
                    </ul> \
                    {% endif %} \
                    {% endfor %} \
                    <!-- Sample resolution progress update to any os --> \
                    <p><br>Our engineers have identified the bug which has only affected the UI and not the accounts themselves. We are currently performing the finals stress tests on the fix. Normal services are expected to resume within x hours.</p> \
                    <p><br>You will continue to receive updates about the progress and be notified once the solution has been deployed. Rest assured that all funds are safe.</p> \
                    <p><br>We remain available if you have any questions</p>'
    )
    agent_instructions = f"To handle all related tickets, please apply a tag corresponding to the device system\nOperating System1: {custom_tags['os1_tag']}\nOperating System2: {custom_tags['os1_tag']}\nUse {incident_summary} Response Macro. This will link all incident tickets accordingly\n\nFor internal communication, please respond to this ticket in private mode. All public comments here will be pushed to all linked incidents."

    # Incident Followers
    followers = [
        {"user_email": "testagent@aidvisor.eu", "action": "put"},
    ]

    # Start Client
    zenpy_client = Zenpy(**config.creds)

    for user in zenpy_client.search(config.creds["email"], type="user"):
        my_user_id = user.id

    # Create macro object
    incident_macro = Macro(
        title=incident_summary + " Response",
        description="Quick reply to " + incident_summary,
        actions=[
            {"field": "current_tags", "value": incident_tag},
            {
                "field": "comment_value_html",
                "value": macro_html,
            },
        ],
    )
    incident_macro.id = zenpy_client.macros.create(incident_macro).id

    # Create ticket object
    problem_ticket = Ticket(
        subject=incident_summary,
        type="problem",
        followers=followers,
        assignee_id=my_user_id,
    )
    problem_ticket.comment = Comment(body=incident_description, public=False)
    problem_ticket.id = zenpy_client.tickets.create(problem_ticket).ticket.id
    problem_ticket.comment = Comment(body=agent_instructions, public=False)
    zenpy_client.tickets.update(problem_ticket)

    # Build a tickets webhook if it does not exist
    if not tickets_webhook:
        # Using requests because zenpy does not support webhooks yet
        webhooks_endpoint = (
            f"https://{config.creds['subdomain']}.zendesk.com/api/v2/webhooks"
        )
        auth = (config.creds["email"] + "/token", config.creds["token"])
        payload = {
            "webhook": {
                "authentication": {
                    "add_position": "header",
                    "data": {"token": config.tickets_token},
                    "type": "bearer_token",
                },
                "description": "Webhook authorized to target Zendesk API tickets endpoint to update ticket properties in a way that is not supported by built-in actions e.g., problem_id",
                "endpoint": "https://"
                + config.creds["subdomain"]
                + ".zendesk.com/api/v2/tickets/{{ticket.id}}",
                "http_method": "PUT",
                "name": "Update Ticket",
                "status": "active",
                "request_format": "json",
                "subscriptions": ["conditional_ticket_events"],
            }
        }
        response = requests.post(
            auth=auth, data=json.dumps(payload), url=webhooks_endpoint
        )
        if response.status_code == 201:
            tickets_webhook = response.json()["webhook"]["id"]
        else:
            logger.error(f"Unexpected Response: {response.text}")

    incident_linking_trigger = Trigger(
        title="Link " + incident_summary + " Incidents",
        conditions={
            "all": [
                {"field": "update_type", "operator": "is", "value": "Change"},
                {
                    "field": "current_tags",
                    "operator": "includes",
                    "value": incident_tag,
                },
                {
                    "field": "current_tags",
                    "operator": "not_includes",
                    "value": "linked_incident",
                },
            ],
        },
        actions=[
            {
                "field": "notification_webhook",
                "value": [
                    tickets_webhook,
                    '{"ticket": {"type": "incident", "problem_id": '
                    + str(problem_ticket.id)
                    + "}}",
                ],
            },
            {"field": "current_tags", "value": "linked_incident"},
        ],
    )
    zenpy_client.triggers.create(incident_linking_trigger)

    if not incident_monitoring_view:
        incident_monitoring_view = View(
            title="Incident Monitoring",
            active=True,
            description='View for recently updated tickets of type "problem"',
            output={
                "group_by": null,
                "group_order": "desc",
                "sort_by": "nice_id",
                "sort_order": "desc",
                "columns": ["nice_id", "subject", "requester", "created", "updated"],
            },
            conditions={
                "all": [
                    {"field": "status", "operator": "less_than", "value": "closed"},
                    {"field": "type", "operator": "is", "value": "problem"},
                    {"field": "updated_at", "operator": "less_than", "value": "720"},
                ]
            },
        )
        incident_monitoring_view.id = zenpy_client.views.create(
            incident_monitoring_view
        ).id

    return


if __name__ == "__main__":
    main()
