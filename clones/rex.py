import sys
import time
import logging
from logging import FileHandler


import schedule

from util.constants import (
    BASEPATH,
    SELL,
    BUY,
    CONSOLIDATED_TRADING,
    TRAILING_STOP_EXECUTE,
    MAY_BUY,
    MAY_SELL,
)

from clones.clone import Clone
from util.utils import load_allowed_stocks, load_slack_channels

sys.path.append(BASEPATH)

LOGGER = logging.getLogger("rex_stream_log")
LOGGER.setLevel(logging.INFO)

(BASEPATH / "logs").mkdir(parents=True, exist_ok=True)
stream_file_handler = FileHandler(str(BASEPATH / "logs" / "rex_stream_activity.log"))
formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(name)s : %(message)s")
stream_file_handler.setFormatter(formatter)
LOGGER.addHandler(stream_file_handler)


class REX(Clone):
    def __init__(
        self,
        navigator=None,
        communicator=None,
        stock_file=None,
        slack_channels_file=None,
    ):
        self.communicator = communicator
        self.navigator = navigator
        self.allowed_stocks = load_allowed_stocks(stocks_file_name=stock_file)
        self.channel_dict = load_slack_channels(slack_channels_file_name=slack_channels_file)
        self.buy_sell_pending_trades = {
            key: {BUY: [], SELL: []} for key in self.allowed_stocks.keys()
        }

    def parse_message(self, message: dict, timestamp: str):
        signals = []

        if "text" in message:
            text_message = message["text"]
            stocks_list = text_message.split("\n\n")
            for stock in stocks_list:
                stock = stock.replace("`", "")
                stock_chunks = stock.split(" ")
                signal = {}
                for stock_chunk in stock_chunks:
                    key, value = stock_chunk.split(":")
                    signal[key] = value

                # filter the signal based on the current timestamp
                if signal["Time"].endswith(timestamp):
                    signals.append(signal)
                else:
                    print(f"Ignored old signal:{signal} @ {timestamp}")

        return signals

    def active_listening(self, interval=5):
        local_time = time.localtime()
        local_time_hour = int(local_time[3])
        local_time_min = int(local_time[4])
        local_time_sec = int(time.localtime()[5])

        if local_time_min % interval == 0 and local_time_sec == 5:
            message = self.communicator.read_message(
                channel=self.channel_dict["short-wave-transmissions"]
            )
            if message is not None:
                signals = self.parse_message(message, f"{local_time_hour}_{local_time_min}_0")

                for signal in signals:
                    if signal["Symbol"] in self.allowed_stocks.keys():
                        allow_trailing_stop = self.allowed_stocks[signal["Symbol"]][
                            "allow_trailing_stop"
                        ]
                        if signal["Decision"] == MAY_BUY:
                            if allow_trailing_stop and signal["trailing_stop_enable"] == True:

                                if (
                                    self.buy_sell_pending_trades[signal["Symbol"]][BUY][-1]
                                    > signal["price"]
                                ):
                                    self.buy_sell_pending_trades[signal["Symbol"]][BUY].append(
                                        signal["Price"]
                                    )
                                    self.buy_sell_pending_trades[signal["Symbol"]][BUY].pop(0)
                                print(
                                    f'Current pending buy trade for {signal["Symbol"]}: {self.buy_sell_pending_trades[signal["Symbol"]][BUY]}'
                                )
                        if signal["Decision"] == BUY:
                            if allow_trailing_stop:
                                self.buy_sell_pending_trades[signal["Symbol"]][BUY].append(
                                    signal["Price"]
                                )
                                print(
                                    f'Current pending buy trade for {signal["Symbol"]}: {self.buy_sell_pending_trades[signal["Symbol"]][BUY]}'
                                )
                            else:
                                self.navigator.buy_stock(
                                    symbol=signal["Symbol"],
                                    price=signal["Price"],
                                    amount=self.allowed_stocks[signal["Symbol"]]["amount"],
                                )

                        if signal["Decision"] == MAY_SELL:
                            if allow_trailing_stop and signal["trailing_stop_enable"] == True:

                                if (
                                    self.buy_sell_pending_trades[signal["Symbol"]][BUY][-1]
                                    < signal["price"]
                                ):
                                    self.buy_sell_pending_trades[signal["Symbol"]][SELL].append(
                                        signal["Price"]
                                    )
                                    self.buy_sell_pending_trades[signal["Symbol"]][SELL].pop(0)
                                print(
                                    f'Current pending sell trade for {signal["Symbol"]}: {self.buy_sell_pending_trades[signal["Symbol"]][SELL]}'
                                )

                        if signal["Decision"] == SELL:
                            if allow_trailing_stop:
                                self.buy_sell_pending_trades[signal["Symbol"]][SELL].append(
                                    signal["Price"]
                                )
                                print(
                                    f'Current pending sell trade for {signal["Symbol"]}: {self.buy_sell_pending_trades[signal["Symbol"]][SELL]}'
                                )
                            else:
                                self.navigator.sell_stock(
                                    symbol=signal["Symbol"],
                                    price=signal["Price"],
                                    amount=self.allowed_stocks[signal["Symbol"]]["amount"],
                                )

                        # trailing stop execute when average buy price is below the current price or average sell price is higher the current price
                        if allow_trailing_stop:
                            current_buy_pending_trades = self.buy_sell_pending_trades[
                                signal["Symbol"]
                            ][BUY]
                            current_sell_pending_trades = self.buy_sell_pending_trades[
                                signal["Symbol"]
                            ][SELL]

                            if signal["trailing_stop_enable"]:
                                if len(current_buy_pending_trades):
                                    buy_average_price = sum(
                                        list(map(float, current_buy_pending_trades))[-2:]
                                    ) / len(current_buy_pending_trades[-2:])

                                    if buy_average_price < float(signal["Price"]):
                                        print(
                                            f'Executing Buy: {buy_average_price} < {signal["Price"]}'
                                        )
                                        signal["Price"] = f"{buy_average_price:.2f}"
                                        signal["Decision"] = TRAILING_STOP_EXECUTE

                                if len(current_sell_pending_trades):
                                    sell_average_price = sum(
                                        list(map(float, current_sell_pending_trades))[-2:]
                                    ) / len(current_sell_pending_trades[-2:])
                                    if sell_average_price > float(signal["Price"]):
                                        print(
                                            f'Executing Sell: {sell_average_price} > {signal["Price"]}'
                                        )
                                        signal["Price"] = f"{sell_average_price:.2f}"
                                        signal["Decision"] = TRAILING_STOP_EXECUTE

                            # trailing stop
                            if signal["Decision"] == TRAILING_STOP_EXECUTE:
                                if len(current_buy_pending_trades) > 0:
                                    print(
                                        f'Executing {signal["Decision"]} buy for {signal["Symbol"]}'
                                    )
                                    for _ in current_buy_pending_trades:
                                        self.navigator.buy_stock(
                                            symbol=signal["Symbol"],
                                            price=signal["Price"],
                                            amount=self.allowed_stocks[signal["Symbol"]]["amount"],
                                        )
                                    self.buy_sell_pending_trades[signal["Symbol"]][BUY] = []

                                if len(current_sell_pending_trades) > 0:
                                    print(
                                        f'Executing {signal["Decision"]} sell for {signal["Symbol"]}'
                                    )
                                    for _ in current_sell_pending_trades:
                                        self.navigator.sell_stock(
                                            symbol=signal["Symbol"],
                                            price=signal["Price"],
                                            amount=self.allowed_stocks[signal["Symbol"]]["amount"],
                                        )
                                    self.buy_sell_pending_trades[signal["Symbol"]][SELL] = []

                        # consolidated trading
                        if (
                            signal["Decision"] == CONSOLIDATED_TRADING
                            and self.allowed_stocks[signal["Symbol"]]["allow_consolidated_trading"]
                        ):
                            amount = (
                                self.allowed_stocks[signal["Symbol"]]["amount"]
                                * self.allowed_stocks[signal["Symbol"]][
                                    "consolidated_trading_multiplier"
                                ]
                            )
                            self.navigator.sell_stock(
                                symbol=signal["Symbol"],
                                price=(
                                    signal["Open"]
                                    if signal["Price"] < signal["Open"]
                                    else signal["Price"]
                                ),
                                amount=amount,
                            )
                            time.sleep(3)
                            self.navigator.buy_stock(
                                symbol=signal["Symbol"],
                                price=(
                                    signal["Open"]
                                    if signal["Price"] > signal["Open"]
                                    else signal["Price"]
                                ),
                                amount=amount,
                            )
                    else:
                        print(f"Skipped {signal['Symbol']} @ {local_time_hour}_{local_time_min}_0")
            else:
                print(f"Error in reading message from Slack")
            self.navigator.refresh_page()
            time.sleep(10)

    def run(self):
        LOGGER.info("Restarting script!")
        try:
            LOGGER.info("Restarting streaming!")
            schedule.every(1).seconds.do(self.active_listening)
            while True:
                schedule.run_pending()
        except Exception as e:
            raise
