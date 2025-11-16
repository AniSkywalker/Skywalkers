import argparse
from typing import List, Optional

from clones.rex import REX

from portfolio_management.web_navigator_clicker import ClickNavigator
from util.communications import SlackClient
from util.utils import load_keys

CLONES = ["REX"]


class Walker:
    def __init__(self, keys):
        self.clones = []
        self.keys = keys
        self.subspace_transceiver = SlackClient(auth=keys["slack_auth_token"])
        self.navigator = None

    def add_crew(self, droid):
        if droid == "REX":
            if self.navigator is None:
                self.navigator = ClickNavigator()

            rex = REX(
                navigator=self.navigator,
                communicator=self.subspace_transceiver,
                stock_file=self.keys["stock_file"],
                slack_channels_file=self.keys["slack_channel_file"],
            )
            self.clones.append(rex)

    def run(self):
        for clone in self.clones:
            clone.run()


def parse_args(arg_list: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Anakin Skywalker goes on a voyage with clones army"
    )
    parser.add_argument(
        "--clones",
        nargs="+",
        type=str,
        choices=CLONES,
        required=False,
        help="Please select clones",
    )
    parser.add_argument(
        "--keys-file",
        type=str,
        required=False,
        help="Name the keys file name with extension",
        default="keys.json",
    )
    return parser.parse_args(arg_list)


if __name__ == "__main__":
    args = parse_args()
    keys = load_keys(args.keys_file)
    walker = Walker(keys)

    if args.clones is None:
        print("WARNING: No crew has been selected.")
    else:

        if args.clones:
            for clone in args.clones:
                print(f"adding {clone}")
                walker.add_crew(clone)

        print("running!!!")
        walker.run()
