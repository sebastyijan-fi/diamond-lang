import functools

class Command:
    def __init__(self, name: str, callback=None, help: str = ""):
        self.name = name
        self.callback = callback
        self.help = help

    def invoke(self, ctx):
        if self.callback is not None:
            return ctx.invoke(self.callback, **ctx.params)

def command(name=None, cls=Command, **attrs):
    def decorator(f):
        cmd_name = name or f.__name__.lower()
        cmd = cls(name=cmd_name, callback=f, **attrs)
        return cmd
    return decorator

@command(name="sync", help="Sync the database.")
def sync_db():
    print("Database synced")
