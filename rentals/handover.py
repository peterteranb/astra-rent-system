"""Use case: the operator hands a reserved unit over to the client and receives it back."""


def register_pickup(rental, staff_user):
    """Record that the client picked up the unit of the rental."""
    raise NotImplementedError


def register_return(rental, staff_user, note):
    """Record that the client returned the unit of the rental."""
    raise NotImplementedError
