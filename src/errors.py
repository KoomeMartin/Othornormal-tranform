"""Exceptions whose messages are safe to show to the user."""


class UserError(Exception):
    """A problem the user can fix (bad input, bad file). Shown in a dialog."""
