import datetime
import os

import pytest
from passari.dpres.events import (CollectionActivityCreationEvent,
                                         LIDOCreationEvent,
                                         MultimediaCreationEvent,
                                         MultimediaMuskettiMigrationEvent,
                                         ObjectCreationEvent,
                                         ObjectMuskettiMigrationEvent)


def get_events_from(event_cls, museum_package):
    event = event_cls(museum_package=museum_package)
    return event.get_events()


@pytest.mark.asyncio
class TestObjectCreationEvent:
    async def test_creation_event_created(self, museum_package_factory):
        museum_package = await museum_package_factory("1234567")

        events = get_events_from(ObjectCreationEvent, museum_package)
        assert events[0].event_type == "creation"
        assert events[0].event_detail == "Object database entry creation"
        assert events[0].event_datetime.year == 1970

    async def test_creation_event_not_created(self, museum_package_factory):
        # Test object 1234571 has no creation date
        museum_package = await museum_package_factory("1234571")

        events = get_events_from(ObjectCreationEvent, museum_package)
        assert not events


@pytest.mark.asyncio
class TestObjectMuskettiMigrationEvent:
    async def test_musketti_migration_event_created(
            self, museum_package_factory):
        museum_package = await museum_package_factory("1234572")

        events = get_events_from(ObjectMuskettiMigrationEvent, museum_package)
        assert events[0].event_type == "transfer"
        assert events[0].event_detail == "Object Musketti migration"
        assert events[0].event_datetime.year == 2018
        assert events[0].event_datetime.month == 11
        assert events[0].event_datetime.day == 5

    async def test_musketti_migration_event_not_created(
            self, museum_package_factory):
        museum_package = await museum_package_factory("1234567")

        events = get_events_from(ObjectMuskettiMigrationEvent, museum_package)
        assert not events


@pytest.mark.asyncio
class TestMultimediaCreationEvent:
    async def test_creation_event_created(self, museum_package_factory):
        museum_package = await museum_package_factory("1234567")

        events = get_events_from(MultimediaCreationEvent, museum_package)
        assert len(events) == 2

        multimedia_ids = ("1234567001", "1234567002")

        for multimedia_id, event in zip(multimedia_ids, events):
            assert event.event_type == "creation"
            assert event.event_detail == "Multimedia creation"
            assert str(event.event_target) == \
                f"attachments/{multimedia_id}/Multimedia.xml"

    async def test_creation_event_not_created(self, museum_package_factory):
        # 1234575 has one attachment without creation date
        museum_package = await museum_package_factory("1234575")

        events = get_events_from(MultimediaCreationEvent, museum_package)
        assert not events


@pytest.mark.asyncio
class TestMultimediaMuskettiMigrationEvent:
    async def test_musketti_migration_event_created(
            self, museum_package_factory):
        museum_package = await museum_package_factory("1234574")

        events = get_events_from(
            MultimediaMuskettiMigrationEvent, museum_package
        )
        assert len(events) == 1

        assert events[0].event_type == "transfer"
        assert events[0].event_detail == "Multimedia Musketti migration"
        assert str(events[0].event_target) == \
            "attachments/1234574001/Multimedia.xml"
        assert events[0].event_datetime.year == 2018
        assert events[0].event_datetime.month == 11
        assert events[0].event_datetime.day == 5

    async def test_musketti_migration_event_not_created(
            self, museum_package_factory):
        museum_package = await museum_package_factory("1234567")

        events = get_events_from(
            MultimediaMuskettiMigrationEvent, museum_package
        )
        assert not events


@pytest.mark.asyncio
class TestCollectionActivityCreationEvent:
    async def test_creation_event_created(self, museum_package_factory):
        # 1234579 has two linked collection activities
        museum_package = await museum_package_factory("1234579")

        events = get_events_from(
            CollectionActivityCreationEvent, museum_package
        )

        multimedia_ids = ("765432001", "765432002")

        for multimedia_id, event in zip(multimedia_ids, events):
            assert event.event_type == "creation"
            assert event.event_detail == "CollectionActivity creation"
            assert str(event.event_target) == \
                f"collection_activities/{multimedia_id}/CollectionActivity.xml"

    async def test_creation_event_not_created(self, museum_package_factory):
        museum_package = await museum_package_factory("1234567")

        events = get_events_from(
            CollectionActivityCreationEvent, museum_package
        )
        assert not events


@pytest.mark.asyncio
class TestLIDOCreationEvent:
    async def test_lido_creation_event_created(
            self, museum_package_factory):
        museum_package = await museum_package_factory("1234567")

        # Give the LIDO document an old modification date
        os.utime(
            museum_package.report_dir / "lido.xml",
            (
                datetime.datetime(2017, 1, 2, 12).timestamp(),
                datetime.datetime(2017, 1, 2, 12).timestamp()
            )
        )

        events = get_events_from(LIDOCreationEvent, museum_package)
        assert len(events) == 1

        assert events[0].event_type == "creation"
        assert events[0].event_detail == "LIDO document creation"
        assert str(events[0].event_target) == "reports/lido.xml"
        assert events[0].event_datetime.year == 2017
        assert events[0].event_datetime.month == 1
        assert events[0].event_datetime.day == 2
