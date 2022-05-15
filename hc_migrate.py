# ZenpyScripts © 2022 by @ahmedsabriz is licensed under
# Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International
# SPDX-License-Identifier: CC-BY-NC-ND-4.0
# https://creativecommons.org/licenses/by-nc-nd/4.0/

from dotenv import load_dotenv
import logging, config
from os import environ
import enum
from zenpy import Zenpy
from zenpy.lib.api_objects import help_centre_objects
from sqlalchemy import null


load_dotenv()

log = logging.getLogger()

creds_source = {
    "email": environ["SOURCE_EMAIL"],
    "token": environ["SOURCE_TOKEN"],
    "subdomain": environ["SOURCE_SUBDOMAIN"],
}
creds_destination = {
    "email": environ["DESTINATION_EMAIL"],
    "token": environ["DESTINATION_TOKEN"],
    "subdomain": environ["DESTINATION_SUBDOMAIN"],
}


class Mapped(enum.Enum):
    permission_groups = 1
    user_segments = 2


# Mapped Lists
permission_groups = []
user_segments = []

# Start Client
zenpy_client_source = Zenpy(**creds_source)
zenpy_client_destination = Zenpy(**creds_destination)


def map_items_by_name(mapped_list, map_type):
    if map_type == Mapped.permission_groups:
        source_items = zenpy_client_source.help_center.permission_groups()
        destination_items = zenpy_client_destination.help_center.permission_groups()
    elif map_type == Mapped.user_segments:
        source_items = zenpy_client_source.help_center.user_segments()
        destination_items = zenpy_client_destination.help_center.user_segments()

    for source_item in source_items:
        for destination_item in destination_items:
            if source_item.name == destination_item.name:
                mapped_list.append((source_item.id, destination_item.id))
                print(
                    map_type,
                    source_item.id,
                    "&",
                    destination_item.id,
                )
    return


def map_items(source_id, mapped_list, map_type):
    for item_tuple in mapped_list:
        if source_id == item_tuple[0]:
            return item_tuple[1]

    if map_type == Mapped.permission_groups:
        source_item = zenpy_client_source.help_center.permission_groups(id=source_id)
        destination_item = (
            zenpy_client_destination.help_center.permission_groups.create(source_item)
        )
    elif map_type == Mapped.user_segments:
        source_item = zenpy_client_source.help_center.user_segments(id=source_id)
        destination_item = zenpy_client_destination.help_center.user_segments.create(
            source_item
        )

    mapped_list.append((source_id, destination_item.id))
    print(
        map_type,
        source_item.id,
        "&",
        destination_item.id,
    )
    return destination_item.id


def add_translation(source_translations, destination_item):
    for translation in source_translations:
        if not translation.locale == destination_item.locale:
            destination_translation = help_centre_objects.Translation(
                body=translation.body,
                draft=translation.draft,
                hidden=translation.hidden,
                locale=translation.locale,
                outdated=translation.outdated,
                title=translation.title,
            )
            if isinstance(destination_item, help_centre_objects.Category):
                destination_translation = (
                    zenpy_client_destination.help_center.categories.create_translation(
                        destination_item, destination_translation
                    )
                )
            elif isinstance(destination_item, help_centre_objects.Section):
                destination_translation = (
                    zenpy_client_destination.help_center.sections.create_translation(
                        destination_item, destination_translation
                    )
                )
            elif isinstance(destination_item, help_centre_objects.Article):
                destination_translation = (
                    zenpy_client_destination.help_center.articles.create_translation(
                        destination_item, destination_translation
                    )
                )
            print("Created", destination_translation)
    return


def migrate():
    for source_category in zenpy_client_source.help_center.categories(
        include=["translations"]
    ):
        destination_category = help_centre_objects.Category(
            description=source_category.description,
            locale=source_category.locale,
            name=source_category.name,
            position=source_category.position,
        )
        destination_category = zenpy_client_destination.help_center.categories.create(
            destination_category
        )
        print("Created", destination_category)
        add_translation(source_category.translations, destination_category)

        for source_section in zenpy_client_source.help_center.sections(
            include=["translations"]
        ):
            destination_section = help_centre_objects.Section(
                category_id=destination_category.id,
                description=source_section.description,
                locale=source_section.locale,
                name=source_section.name,
                parent_section_id=None,  # TODO
                position=source_section.position,
            )
            destination_section = zenpy_client_destination.help_center.sections.create(
                destination_section
            )
            print("Created", destination_section)
            add_translation(source_section.translations, destination_section)

            for source_article in zenpy_client_source.help_center.articles(
                include=["translations"]
            ):
                destination_article = help_centre_objects.Article(
                    author_id=zenpy_client_destination.users.me().id,  # TODO
                    body=source_article.body,
                    comments_disabled=source_article.comments_disabled,
                    label_names=source_article.label_names,
                    locale=source_article.locale,
                    permission_group_id=map_items(
                        source_article.permission_group_id,
                        permission_groups,
                        Mapped.permission_groups,
                    ),
                    position=source_article.position,
                    promoted=source_article.promoted,
                    section_id=destination_section.id,
                    title=source_article.title,
                    user_segment_id=null
                    if not source_article.user_segment_id
                    else map_items(
                        source_article.user_segment_id,
                        user_segments,
                        Mapped.user_segments,
                    ),
                )
                destination_article = (
                    zenpy_client_destination.help_center.articles.create(
                        destination_section.id, destination_article
                    )
                )
                print("Created ", destination_article)
                add_translation(source_article.translations, destination_article)
    return


def clean_up(key):
    for item in key():
        key.delete(item)
        print("Deleted", item)


def main():
    map_items_by_name(permission_groups, Mapped.permission_groups)
    map_items_by_name(user_segments, Mapped.user_segments)
    # clean_up(zenpy_client_destination.help_center.sections)
    # clean_up(zenpy_client_destination.help_center.categories)
    # clean_up(zenpy_client_destination.help_center.articles)
    migrate()
    return


if __name__ == "__main__":
    main()
