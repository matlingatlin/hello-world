"""A long silence must not look like a dead connection.

A real build is quiet for minutes: Layer B, then Layer C, then the first
package, before a single progress event exists. Node's fetch (undici) gives up
on a response body after 300 seconds of silence — so a build whose first event
took 313 seconds was killed mid-flight and the user was told "The build
stopped" about a build that was working perfectly.

It could only ever show up on a real run: with fake providers nothing is quiet
for five minutes.
"""

from __future__ import annotations

import asyncio

import pytest

from scio_engine.main import with_heartbeat

pytestmark = pytest.mark.anyio


async def collect(source, every: float) -> list[str]:
    return [chunk async for chunk in with_heartbeat(source, every=every)]


class TestTheHeartbeat:
    async def test_a_silent_source_still_says_something(self):
        async def slow():
            await asyncio.sleep(0.25)
            yield "event: started\ndata: {}\n\n"

        chunks = await collect(slow(), every=0.05)

        assert chunks[-1] == "event: started\ndata: {}\n\n"
        assert all(c == ": keep-alive\n\n" for c in chunks[:-1])
        assert len(chunks) > 1, "nothing was sent during a quarter-second silence"

    async def test_the_events_themselves_are_untouched(self):
        async def quick():
            yield "event: a\ndata: 1\n\n"
            yield "event: b\ndata: 2\n\n"

        assert await collect(quick(), every=5.0) == [
            "event: a\ndata: 1\n\n",
            "event: b\ndata: 2\n\n",
        ]

    async def test_the_work_in_flight_is_never_cancelled(self):
        """The timeout is a moment to speak, not a reason to give up: the
        pending step is shielded, so a slow package still finishes."""
        finished: list[str] = []

        async def slow():
            await asyncio.sleep(0.2)
            finished.append("one")
            yield "event: done\ndata: {}\n\n"

        chunks = await collect(slow(), every=0.02)

        assert finished == ["one"]
        assert chunks[-1] == "event: done\ndata: {}\n\n"

    async def test_an_empty_source_ends_cleanly(self):
        async def nothing():
            return
            yield  # pragma: no cover

        assert await collect(nothing(), every=0.01) == []

    def test_a_keepalive_is_a_comment_the_client_ignores(self):
        """`:` frames carry no `data:`, so every SSE reader drops them — which
        is what makes this safe to add to a stream with real consumers."""
        frame = ": keep-alive\n\n"

        assert frame.startswith(":")
        assert "data:" not in frame
