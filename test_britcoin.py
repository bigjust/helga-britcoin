import mock
import unittest

from helga_britcoin import BritBlock, BritChain, proof_of_work


class PluginTest(unittest.TestCase):

    def setUp(self):
        self.blockchain = BritChain()

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

    @mock.patch('helga_britcoin.work')
    def test_mine_successful(self, mock_work):
        """
        If mining is successful, test that the miner gets credit.
        """

        mock_work.return_value = '00'

        output = self.blockchain.mine('bigjust', 'test message')
        last_block = self.blockchain.latest_block()

        self.assertIsNotNone(output)
        self.assertEquals(len(last_block.data['transactions']), 1)
        self.assertEquals(last_block.data['transactions'][0]['to'], 'bigjust')


    @mock.patch('helga_britcoin.work')
    def test_mine_unsuccessful(self, mock_work):
        """
        if mining is unsuccessful, nothing happens.
        """

        mock_work.return_value = '01'
        output = self.blockchain.mine('bigjust', 'test message')

        self.assertIsNone(output)
