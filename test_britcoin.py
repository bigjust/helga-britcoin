import mock
import unittest

from helga_britcoin import BritcoinBlock, proof_of_work


class PluginTest(unittest.TestCase):

    def setUp(self):
        pass

    @mock.patch('helga_britcoin.work')
    def test_proofer_successful(self, mock_work):
        """
        Make sure proof function returns hash attempt if successful.
        """

        mock_work.return_value = '00abcd'
        attempt = proof_of_work('00aaaa', 'test message')

        self.assertIsNotNone(attempt)

    @mock.patch('helga_britcoin.work')
    def test_proofer_unsuccessful(self, mock_work):
        """
        Make sure proof function returns None for bad attempt.
        """

        mock_work.return_value = '1234abcd'
        attempt = proof_of_work('00aaaa', 'test message')

        self.assertIsNone(attempt)
