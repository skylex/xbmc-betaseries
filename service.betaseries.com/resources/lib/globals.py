# -*- coding: utf-8 -*-
#

# Declaration to integrate same serviceApi instance for all system
betaseriesapi = None


class Service:
    """Describes settings"""

    def __init__(
        self,
        active,
        first,
        user,
        password,
        bulk,
        mark,
        unMark,
        follow,
        notify,
        update,
    ):
        self.name = "Betaseries"
        self.active = active
        self.first = first
        self.user = user
        self.password = password
        self.bulk = bulk
        self.mark = mark
        self.unMark = unMark
        self.follow = follow
        self.notify = notify
        self.update = update
