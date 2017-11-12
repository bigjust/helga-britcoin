
import mock
import unittest

from freezegun import freeze_time

from helga_britcoin import BritBlock, BritChain, proof_of_conversation, work


class BritcoinPluginTest(unittest.TestCase):

    @mock.patch('helga_britcoin.db')
    def setUp(self, mock_db):
        db = mock_db.britcoin.find.return_value
        db.sort.return_value = []

        self.blockchain = BritChain()

    @mock.patch('helga_britcoin.work')
    def test_proofer_successful(self, mock_work):
        """
        Make sure proof function returns hash attempt if successful.
        """

        mock_work.return_value = '00abcd'
        attempt = proof_of_conversation('00aaaa', 'test message')

        self.assertIsNotNone(attempt)

    @mock.patch('helga_britcoin.work')
    def test_proofer_unsuccessful(self, mock_work):
        """
        Make sure proof function returns None for bad attempt.
        """

        mock_work.return_value = '1234abcd'
        attempt = proof_of_conversation('00aaaa', 'test message')

        self.assertIsNone(attempt)

    @mock.patch('helga_britcoin.db')
    @mock.patch('helga_britcoin.work')
    def test_mine_successful(self, mock_work, mock_db):
        """
        If mining is successful, test that the miner gets credit.
        """

        mock_work.return_value = '00'
        output = self.blockchain.mine('bigjust', 'test message')
        last_block = self.blockchain.latest_block()

        mock_db.britcoin.insert.assert_called_with(last_block.__dict__)
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

    def test_britcoin_balances(self):

        self.blockchain.append(
            BritBlock(
                0, 0,
                {'transactions': [{
                    'from': 'network',
                    'to': 'brit',
                    'amount': 1
                },{
                    'from': 'network',
                    'to': 'bigjust',
                    'amount': 2
                }
                ]},
                "0"
            ))

        self.blockchain.append(
            BritBlock(
                0, 0,
                {'transactions': [{
                    'from': 'bigjust',
                    'to': 'brit',
                    'amount': 1
                }]},
                "0"
            ))

        balances = self.blockchain.calculate_balances()

        self.assertEqual(balances['brit'], 2)
        self.assertEqual(balances['bigjust'], 1)
        self.assertEqual(balances['network'], -3)


    def test_genesis_block_creation(self):
        """
        Test that the genesis block gets created on an empty
        blockchain.
        """

        self.assertEqual(len(self.blockchain), 1)

    @mock.patch('helga_britcoin.db')
    def test_genesis_block_defer(self, mock_db):
        """
        Test that the genesis block doesn't get created if a
        blockchain is being retrieved from storage.
        """

        genesis_block = {
            'index': 0,
            'timestamp': 'now',
            'data': 'from db',
            'previous_hash': '0',
        }

        db = mock_db.britcoin.find.return_value
        db.sort.return_value = [genesis_block]

        blockchain = BritChain()

        self.assertEqual(len(blockchain), 1)
        self.assertEqual(blockchain[0].data, 'from db')

    @mock.patch('helga_britcoin.db')
    def test_load_blockchain(self, mock_db):
        """
        Tests loading and verifying blockchain from mocked data
        store. The third block will fail verification, leaving two
        verified blocks in the chain.
        """

        genesis_block = {
            'index': 0,
            'timestamp': 'now',
            'data': 'from db',
            'previous_hash': '0',
        }

        second_block = {
            'index': 1,
            'timestamp': 'now',
            'data': 'another from db',
            'previous_hash': 'cb8c80e8f7311d050c078021c38382bfc3c3a6ad9fb2255cbe619de54703df8e',
        }

        third_block = {
            'index': 2,
            'timestamp': 'now',
            'data': 'tampered block',
            'previous_hash': 'bleh',
        }

        db = mock_db.britcoin.find.return_value
        db.sort.return_value = [genesis_block, second_block, third_block]

        blockchain = BritChain()

        self.assertEqual(len(blockchain), 2)
        self.assertEqual(blockchain[1].data, 'another from db')


    def test_order_in_hash(self):
        """
        Make sure that arbitrary ordering in dictionary elements results in the same hash.
        """

        block1_data = {
            'proof-of-work': 'work_did',
            'transactions': [{
                'to': 'bigjust',
                'from': 'brit',
                'amount': 9000,
            }],
        }

        block2_data = {
            'transactions': [{
                'from': 'brit',
                'amount': 9000,
                'to': 'bigjust',
            }],
            'proof-of-work': 'work_did',
        }

        block1 = BritBlock(0, 'nowish', block1_data, 'abcd')
        block2 = BritBlock(0, 'nowish', block2_data, 'abcd')

        self.assertEqual(block1.hash, block2.hash)

    def test_work_function(self):
        """
        Make sure work works.
        """

        self.assertEqual(
            work('abc', 'message'),
            '52a86b9b940a0539ffe8fa4517fb3569329b7219d0c74d82b2130d0f0dff56d1',
        )


@freeze_time("2016-11-07 13:00:00")
class BritcoinPluginStatsTest(BritcoinPluginTest):

    def test_stats(self):
        """
        make sure the stats we care about are included in the output
        """

        self.blockchain.append(
            BritBlock(
                0, '2016-11-07 10:00:00',
                {'transactions': [{
                    'from': 'network',
                    'to': 'brit',
                    'amount': 90
                },{
                    'from': 'network',
                    'to': 'bigjust',
                    'amount': 60
                }
                ]},
                "0"
            ))

        self.blockchain.append(
            BritBlock(
                0, '2016-11-07 11:00:00',
                {'transactions': [{
                    'from': 'bigjust',
                    'to': 'brit',
                    'amount': 1
                }]},
                "0"
            ))


        stats_message = self.blockchain.stats()

        self.assertIn('150 britcoins', stats_message)
        self.assertIn('48 seconds', stats_message)
