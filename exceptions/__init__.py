from discord.ext import commands

class ChannelNotSet(commands.CheckFailure):
    """
    Thrown when a user is attempting a command on a channel that the bot doesn't know about
    """

    def __init__(self, message="Command on unknown channel!"):
        self.message = message
        super().__init__(self.message)

class NotInGuild(commands.CheckFailure):
    """
    Thrown when a user is attempting a command in an unknown guild
    """

    def __init__(self, message="Command on unknown guild!"):
        self.message = message
        super().__init__(self.message)

class UserNotOwner(commands.CheckFailure):
    """
    Thrown when a user is attempting something, but is not an owner of the bot.
    """

    def __init__(self, message="User is not an owner of the bot!"):
        self.message = message
        super().__init__(self.message)

class UserNotAdmin(commands.CheckFailure):
    """
    Thrown when a user is attempting something, but is not an admin.
    """

    def __init__(self, message="User is not an admin!"):
        self.message = message
        super().__init__(self.message)
