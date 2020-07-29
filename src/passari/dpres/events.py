from passari.utils import unix_timestamp_to_datetime


class PremisEvent:
    def __init__(
            self, event_type, event_outcome, event_detail,
            event_datetime=None, event_target=None, event_outcome_detail=None):
        self.event_type = event_type
        self.event_outcome = event_outcome
        self.event_detail = event_detail
        self.event_datetime = event_datetime
        self.event_target = event_target
        self.event_outcome_detail = event_outcome_detail


class EventCreator(object):
    """
    Base class that generates PREMIS events from a MuseumObjectPackage
    """
    def __init__(self, museum_package):
        self.museum_package = museum_package
        self.museum_object = museum_package.museum_object

    def get_events(self):
        raise NotImplementedError


class ObjectCreationEvent(EventCreator):
    """
    Creates creation event for the museum object
    """
    def get_events(self):
        if self.museum_object.created_date:
            return [
                PremisEvent(
                    event_type="creation",
                    event_datetime=self.museum_object.created_date,
                    event_detail="Object database entry creation",
                    event_outcome_detail=(
                        "Object creation date in the MuseumPlus collection "
                        "management system administrated by Finnish Museums "
                        "Association"
                    ),
                    event_outcome="success"
                )
            ]

        return None


class MultimediaCreationEvent(EventCreator):
    """
    Creates creation events for the Multimedia entries
    """
    def get_events(self):
        events = []

        for attachment in self.museum_package.attachments:
            if not attachment.created_date:
                continue

            xml_path = (
                self.museum_package.attachment_dir
                / str(attachment.attachment_id)
                / "Multimedia.xml"
            ).relative_to(self.museum_package.sip_dir)

            events.append(
                PremisEvent(
                    event_type="creation",
                    event_datetime=attachment.created_date,
                    event_detail="Multimedia creation",
                    event_outcome_detail=(
                        "Multimedia creation date in the MuseumPlus "
                        "collection management system administrated by "
                        "Finnish Museums Association"
                    ),
                    event_outcome="success",
                    event_target=xml_path,
                )
            )

        return events


class ObjectMuskettiMigrationEvent(EventCreator):
    """
    Creates migration event for the museum object if it was migrated from
    Musketti
    """
    def get_events(self):
        if not self.museum_object.created_date:
            return []

        # Migration happened during 11/2018
        is_migration_date = (
            self.museum_object.created_date.month == 11
            and self.museum_object.created_date.year == 2018
        )

        # Migrated objects have the creator "ZET_DÜ"
        is_migration_user = self.museum_object.created_user == "ZET_DÜ"

        if is_migration_date and is_migration_user:
            return [
                PremisEvent(
                    # 'transfer' event type recommended by CSC staff instead
                    # of 'migration', which has different meaning in this
                    # context
                    event_type="transfer",
                    event_datetime=self.museum_object.created_date,
                    event_detail="Object Musketti migration",
                    event_outcome_detail=(
                        "Object migrated to MuseumPlus collection management "
                        "system from Musketti"
                    ),
                    event_outcome="success"
                )
            ]

        return []


class MultimediaMuskettiMigrationEvent(EventCreator):
    """
    Creates migration event for the Multimedia object if it was migrated from
    Musketti
    """
    def get_events(self):
        events = []

        for attachment in self.museum_package.attachments:
            if not attachment.created_date:
                continue

            # Migration happened during 11/2018
            is_migration_date = (
                attachment.created_date.month == 11
                and attachment.created_date.year == 2018
            )

            # Migrated objects have the creator "ZET_DÜ"
            is_migration_user = attachment.created_user == "ZET_DÜ"

            if is_migration_date and is_migration_user:
                xml_path = (
                    self.museum_package.attachment_dir
                    / str(attachment.attachment_id)
                    / "Multimedia.xml"
                ).relative_to(self.museum_package.sip_dir)

                events.append(
                    PremisEvent(
                        # 'transfer' event type recommended by CSC staff instead
                        # of 'migration', which has different meaning in this
                        # context
                        event_type="transfer",
                        event_datetime=attachment.created_date,
                        event_detail="Multimedia Musketti migration",
                        event_outcome_detail=(
                            "Multimedia migrated to MuseumPlus collection "
                            "management system from Musketti"
                        ),
                        event_outcome="success",
                        event_target=xml_path
                    )
                )

        return events


class CollectionActivityCreationEvent(EventCreator):
    """
    Creates creation events for the CollectionActivity entries
    """
    def get_events(self):
        events = []

        for col_activity in self.museum_package.collection_activities:
            if not col_activity.created_date:
                continue

            xml_path = (
                self.museum_package.collection_activity_dir
                / str(col_activity.collection_activity_id)
                / "CollectionActivity.xml"
            ).relative_to(self.museum_package.sip_dir)

            events.append(
                PremisEvent(
                    event_type="creation",
                    event_datetime=col_activity.created_date,
                    event_detail="CollectionActivity creation",
                    event_outcome_detail=(
                        "CollectionActivity creation date in the MuseumPlus "
                        "database administrated by Finnish Museums "
                        "Association. "
                    ),
                    event_outcome="success",
                    event_target=xml_path,
                )
            )

        return events


class LIDOCreationEvent(EventCreator):
    """
    Creates event for the creation of the LIDO document
    """
    def get_events(self):
        return [
            PremisEvent(
                event_type="creation",
                # The modification date of lido.xml shuold be almost identical
                # to the time it was created by MuseumPlus
                event_datetime=unix_timestamp_to_datetime(
                    (self.museum_package.report_dir
                     / "lido.xml").stat().st_mtime
                ),
                event_detail="LIDO document creation",
                event_outcome_detail=(
                    "LIDO document generated in the MuseumPlus service from "
                    "the Object using a MuseumPlus Template."
                ),
                event_target=(
                    (self.museum_package.report_dir / "lido.xml")
                    .relative_to(self.museum_package.sip_dir)
                ),
                event_outcome="success"
            )
        ]


EVENTS = (
    ObjectCreationEvent, MultimediaCreationEvent, ObjectMuskettiMigrationEvent,
    MultimediaMuskettiMigrationEvent, CollectionActivityCreationEvent,
    LIDOCreationEvent
)

# TODO: Check for other event creators enabled using setuptools' entrypoint
# feature. This would allow events to be developed and deployed without having
# to fork 'passari' itself.


def get_premis_events(museum_package):
    """
    Get all applicable PREMIS events for a MuseumObjectPackage
    """
    events = []
    for event_cls in EVENTS:
        event_creator = event_cls(museum_package=museum_package)
        events += event_creator.get_events()

    return events
