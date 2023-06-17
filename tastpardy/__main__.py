import click

from tastpardy.config import Config
from tastpardy.irc import TastyIRCBot


@click.command()
@click.option(
    "--config",
    required=True,
    help="Path to a config file in the style of configexample.json",
)
def tastpardy(config: str):
    """Tasty game and chat bot!"""
    try:
        with open(config) as f:
            conf = Config.from_json(f.read()) # type: ignore
    except FileNotFoundError:
        print(
            "Config file not found. Please create a config file in the style of configexample.json."
        )
        exit(1)
    except Exception as e:
        print("Unknown error: {}".format(e))
        raise e

    # TODO: Add config for, or based on contents on config, do more than a single
    # IRC bot. For now, everything assumes exactly one IRC bot.
    if not conf or not conf.irc or len(conf.irc) != 1:
        raise NotImplementedError("Exactly one IRC bot is currently supported.")

    TastyIRCBot(dbpath=conf.dbpath, conf=conf.irc[0]).start()


if __name__ == "__main__":
    tastpardy()
