from typing import Protocol


class UoWPort[SessionType](Protocol):
    """
    Interface for the Unit of Work.
    Provides access to the transactional session.
    """
    session: SessionType
