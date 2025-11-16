"""
Web navigator through clicking that imitates the buy/sell through positioned clicks on Trading212
"""

import time
import pyautogui
from util.utils import load_anchors


class ClickNavigator:
    def __init__(self):
        self.anchors = load_anchors("anchors.json")

    def navigate_to_portfolio(self):
        self.button_click(key="portfolio")

    def refresh_page(self):
        self.button_click(key="page_refresh")

    def navigate_to_stock(self, symbol):
        self.button_click(key=symbol)

    def button_click(self, key, clicks=1):
        pyautogui.moveTo(self.anchors[key]["x"], self.anchors[key]["y"])
        pyautogui.click(clicks=clicks)

    def assign_value(self, value):
        for _ in range(20):
            pyautogui.press("right")
        for _ in range(20):
            pyautogui.press("backspace")
        pyautogui.write(f"{value}", interval=0.1)

    def buy_stock(self, symbol, price, amount, order_type="LIMIT"):
        try:
            self.navigate_to_stock(symbol)
            time.sleep(3)
            print(f"Navigated to {symbol}!!")

            self.button_click(key="buy_button")
            time.sleep(3)
            print(f"Buy clicked!!")

            if order_type == "MARKET":
                self.button_click(key="market_button")
                time.sleep(3)

                self.button_click(key="amount", clicks=2)
                time.sleep(3)

                self.assign_value(amount)
            else:
                self.button_click(key="limit_button")
                time.sleep(3)

                self.button_click(key="amount", clicks=2)
                time.sleep(3)

                self.assign_value(amount)
                time.sleep(1)

                self.button_click(key="price", clicks=2)
                time.sleep(3)

                self.assign_value(price)
                time.sleep(3)

            print(f"Value added!!")
            time.sleep(3)

            self.button_click(key="review_order_button")
            print(f"Order reviewed!!")
            time.sleep(3)

            self.button_click(key="send_order_button")
            print(f"Order sent!!")
            time.sleep(3)

            self.button_click(key="order_placed_ok_button")

            print(f"Returned to portfolio!!")
            time.sleep(3)
        except Exception as e:
            print(f"Buy execution failed for {amount} {symbol} @ {price}!!!")
            print(e)
            self.refresh_page()
            print(f"Page refreshed!!")

    def sell_stock(self, symbol, price, amount, order_type="LIMIT"):
        try:
            self.navigate_to_stock(symbol)
            print(f"Navigated to {symbol}!!")
            time.sleep(3)

            self.button_click(key="sell_button")
            print(f"Sell clicked!!")
            time.sleep(3)

            if order_type == "MARKET":
                self.button_click(key="market_button")
                time.sleep(3)

                self.button_click(key="amount", clicks=2)
                time.sleep(3)

                self.assign_value(amount)
            else:
                self.button_click(key="limit_button")
                time.sleep(3)

                self.button_click(key="amount", clicks=2)
                time.sleep(3)

                self.assign_value(amount)
                time.sleep(1)

                self.button_click(key="price", clicks=2)
                time.sleep(3)

                self.assign_value(price)
                time.sleep(3)

            print(f"Value added!!")
            time.sleep(3)

            self.button_click(key="review_order_button")
            print(f"Order reviewed!!")
            time.sleep(3)

            self.button_click(key="send_order_button")
            print(f"Order sent!!")
            time.sleep(3)

            self.button_click(key="order_placed_ok_button")

            print(f"Returned to portfolio!!")
            time.sleep(3)

        except Exception as e:
            print(f"Sell execution failed for {amount} {symbol} @ {price}!!!")
            print(e)
            self.refresh_page()
            print(f"Page refreshed!!")


if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.getcwd())
    from util.utils import load_keys

    keys = load_keys("keys.json")
    navigator = ClickNavigator()
    time.sleep(5)
    navigator.navigate_to_portfolio()
    # navigator.navigate_to_stock("TSLA_US_EQ")
    # navigator.sell_stock(symbol="TSLA_US_EQ", price=500, amount=0.01)
    navigator.refresh_page()
