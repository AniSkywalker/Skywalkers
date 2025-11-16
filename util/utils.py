import json
from pathlib import Path


def load_keys(keys_file_name):
    return json.load(open(Path(__file__).parent.parent / keys_file_name))


def load_anchors(anchors_file_name):
    return json.load(open(Path(__file__).parent.parent / anchors_file_name))


def load_allowed_stocks(stocks_file_name):
    return json.load(open(Path(__file__).parent.parent / stocks_file_name))


def load_slack_channels(slack_channels_file_name):
    return json.load(open(Path(__file__).parent.parent / slack_channels_file_name))
