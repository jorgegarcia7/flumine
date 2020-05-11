import unittest
from unittest import mock

from flumine.baseflumine import BaseFlumine


class BaseFlumineTest(unittest.TestCase):
    def setUp(self):
        self.mock_client = mock.Mock()
        self.base_flumine = BaseFlumine(self.mock_client)

    def test_init(self):
        self.assertFalse(self.base_flumine.BACKTEST)
        self.assertEqual(self.base_flumine.client, self.mock_client)
        self.assertFalse(self.base_flumine._running)
        self.assertEqual(self.base_flumine._logging_controls, [])
        self.assertEqual(len(self.base_flumine._trading_controls), 2)
        self.assertEqual(self.base_flumine._workers, [])

    def test_run(self):
        with self.assertRaises(NotImplementedError):
            self.base_flumine.run()

    def test_add_strategy(self):
        mock_strategy = mock.Mock()
        self.base_flumine.add_strategy(mock_strategy)
        self.assertEqual(len(self.base_flumine.strategies), 1)
        self.assertEqual(len(self.base_flumine.streams), 1)

    def test_add_worker(self):
        mock_worker = mock.Mock()
        self.base_flumine.add_worker(mock_worker)
        self.assertEqual(len(self.base_flumine._workers), 1)

    def test_add_client_control(self):
        self.mock_client.trading_controls = []
        mock_control = mock.Mock()
        self.base_flumine.add_client_control(mock_control)
        self.assertEqual(
            self.base_flumine.client.trading_controls,
            [mock_control(self.base_flumine, self.mock_client)],
        )

    def test_add_trading_control(self):
        mock_control = mock.Mock()
        self.base_flumine.add_trading_control(mock_control)
        self.assertEqual(len(self.base_flumine._trading_controls), 3)

    def test__add_default_workers(self):
        self.base_flumine._add_default_workers()
        self.assertEqual(len(self.base_flumine._workers), 0)

    def test__process_market_books(self):
        mock_event = mock.Mock()
        mock_market_book = mock.Mock()
        mock_market_book.runners = []
        mock_event.event = [mock_market_book]
        self.base_flumine._process_market_books(mock_event)

    def test__process_market_orders(self):
        mock_market = mock.Mock()
        mock_market.blotter.process_orders.return_value = [1, 2, 3]
        self.base_flumine._process_market_orders(mock_market)
        mock_market.blotter.process_orders.assert_called_with(self.mock_client)

    def test__process_order_package(self):
        mock_trading_control = mock.Mock()
        self.base_flumine._trading_controls = [mock_trading_control]
        mock_client_trading_control = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.market_id = "1.123"
        mock_order_package.client.trading_controls = [mock_client_trading_control]
        self.base_flumine._process_order_package(mock_order_package)
        mock_order_package.client.execution.handler.assert_called_with(
            mock_order_package
        )
        mock_trading_control.assert_called_with(mock_order_package)
        mock_client_trading_control.assert_called_with(mock_order_package)

    def test__process_order_package_empty(self):
        mock_client_trading_control = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.market_id = "1.123"
        mock_order_package.client.trading_controls = [mock_client_trading_control]
        mock_order_package.info = {}
        mock_order_package.orders = []
        self.base_flumine._trading_controls = []
        self.base_flumine._process_order_package(mock_order_package)
        mock_order_package.client.execution.handler.assert_not_called()

    def test__process_order_package_controls(self):
        mock_trading_control = mock.Mock()
        mock_client_control = mock.Mock()
        self.base_flumine._trading_controls = [mock_trading_control]
        mock_client_trading_control = mock.Mock()
        mock_order_package = mock.Mock()
        mock_order_package.market_id = "1.123"
        mock_order_package.client.trading_controls = [mock_client_trading_control]
        mock_order_package.info = {}
        mock_order_package.orders = []
        mock_order_package.client.trading_controls = [mock_client_control]
        self.base_flumine._process_order_package(mock_order_package)
        mock_order_package.client.execution.handler.assert_not_called()
        mock_trading_control.assert_called_with(mock_order_package)
        mock_client_control.assert_called_with(mock_order_package)

    @mock.patch("flumine.baseflumine.Market")
    def test__add_live_market(self, mock_market):
        mock_market_book = mock.Mock()
        self.assertEqual(
            self.base_flumine._add_live_market("1.234", mock_market_book), mock_market()
        )
        self.assertEqual(len(self.base_flumine.markets._markets), 1)

    def test__process_raw_data(self):
        mock_event = mock.Mock()
        mock_event.event = (12, 12345, {})
        self.base_flumine._process_raw_data(mock_event)

    def test__process_current_orders(self):
        mock_event = mock.Mock()
        mock_current_orders = mock.Mock()
        mock_current_orders.orders = []
        mock_event.event = [mock_current_orders]
        self.base_flumine._process_current_orders(mock_event)

    def test__process_end_flumine(self):
        self.base_flumine._process_end_flumine()

    def test_enter_exit(self):
        control = mock.Mock()
        self.base_flumine._logging_controls = [control]
        self.base_flumine.simulated_execution = mock.Mock()
        self.base_flumine.betfair_execution = mock.Mock()
        with self.base_flumine:
            self.assertTrue(self.base_flumine._running)
            self.mock_client.login.assert_called_with()

        self.assertFalse(self.base_flumine._running)
        self.mock_client.logout.assert_called_with()
        self.base_flumine.simulated_execution.shutdown.assert_called_with()
        self.base_flumine.betfair_execution.shutdown.assert_called_with()
        control.start.assert_called_with()
