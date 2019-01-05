# -*- coding: utf-8 -*-
#
# Copyright 2017 Ricequant, Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rqalpha.interface import AbstractFrontendValidator
from rqalpha.const import SIDE, POSITION_EFFECT, DEFAULT_ACCOUNT_TYPE
from rqalpha.utils.logger import user_system_log

from rqalpha.utils.i18n import gettext as _


class CashValidator(AbstractFrontendValidator):
    def __init__(self, env):
        self._env = env

    def _stock_validator(self, account, order):
        if order.side == SIDE.SELL:
            return True
        frozen_value = order.frozen_price * order.quantity
        cost_money = frozen_value + self._env.get_order_transaction_cost(DEFAULT_ACCOUNT_TYPE.STOCK, order)
        if cost_money <= account.cash:
            return True

        user_system_log.warn(
            _("Order Creation Failed: not enough money to buy {order_book_id}, needs {cost_money:.2f}, "
              "cash {cash:.2f}").format(
                order_book_id=order.order_book_id,
                cost_money=cost_money,
                cash=account.cash,
            )
        )
        return False

    def _future_validator(self, account, order):
        if order.position_effect != POSITION_EFFECT.OPEN:
            return True

        instrument = self._env.get_instrument(order.order_book_id)
        margin = order.frozen_price * order.quantity * instrument.contract_multiplier * instrument.margin_rate
        cost_money = margin * self._env.config.base.margin_multiplier
        cost_money += self._env.get_order_transaction_cost(DEFAULT_ACCOUNT_TYPE.FUTURE, order)
        if cost_money <= account.cash:
            return True

        user_system_log.warn(
            _("Order Creation Failed: not enough money to buy {order_book_id}, needs {cost_money:.2f},"
              " cash {cash:.2f}").format(
                order_book_id=order.order_book_id,
                cost_money=cost_money,
                cash=account.cash,
            )
        )
        return False

    def can_submit_order(self, order, account=None):
        if account is None:
            return True
        if account.type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
            return self._stock_validator(account, order)
        elif account.type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
            return self._future_validator(account, order)
        else:
            return True

    def can_cancel_order(self, order, account=None):
        return True
