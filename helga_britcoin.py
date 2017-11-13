import datetime as date
import hashlib
import humanize
import pymongo

from collections import defaultdict, OrderedDict

from helga import settings, log
from helga.db import db
from helga.plugins import Command


logger = log.getLogger(__name__)
blockchain = None
DIFFICULTY = int(getattr(settings, 'BRITCOIN_DIFFICULTY', 2))
IGNORED = getattr(settings, 'IGNORED', [])
INITIAL_DATA = getattr(settings, 'BRITCOIN_INITIAL_DATA', {'data': 'Genesis Block'})
DEBUG = getattr(settings, 'HELGA_DEBUG', False)
CMD_PREFIX = getattr(settings, 'COMMAND_PREFIX_CHAR', '!')


def timestamp2datetime(timestamp):
    return date.datetime.strptime(
        timestamp,
        '%Y-%m-%d %H:%M:%S'
    )

def work(prev_hash, message):
    """
    hash the message with the previous hash to produce the hash
    attempt.
    """

    hasher = hashlib.sha256()
    hasher.update(prev_hash + message)
    hash_attempt = hasher.hexdigest()

    return hash_attempt

def proof_of_conversation(prev_hash, message):
    """
    r/AnAttemptWasMade
    """

    attempt = work(prev_hash, message)

    if attempt.startswith('0' * DIFFICULTY):
        return attempt


class BritBlock(object):

    def __init__(self, index, timestamp, data, previous_hash):

        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):

        sha = hashlib.sha256()

        if isinstance(self.data, dict):
            data = OrderedDict(sorted(self.data.items(), key=lambda t: t[0]))
        else:
            data = self.data

        block_to_hash = str(self.index) +\
            str(self.timestamp) +\
            str(data) +\
            str(self.previous_hash)

        sha.update(block_to_hash)

        return sha.hexdigest()


class BritChain(list):

    def __init__(self):
        """
        Load blocks from mongodb. If none are found, create a genesis
        block.
        """

        super(BritChain, self).__init__()

        self.pending_transactions = []

        for block in db.britcoin.find().sort([('index', pymongo.ASCENDING)]):

            potential_block = BritBlock(
                block['index'],
                block['timestamp'],
                block['data'],
                block['previous_hash']
            )

            if block['index'] > 0:
                logger.debug('verifying block index = {}'.format(block['index']))

                if self[block['index'] - 1].hash == block['previous_hash']:
                    self.append(potential_block)
                else:
                    logger.debug('invalid block found: {}'.format(
                        potential_block.__dict__
                    ))
            else:
                self.append(potential_block)

        if not len(self):
            self.create_genesis_block()

    def append(self, block, persist=False):
        """
        When blocks are added to the chain, add the block to mongodb.
        """

        super(BritChain, self).append(block)

        if persist:
            logger.debug('adding block: {}'.format(block.__dict__))
            db.britcoin.insert(block.__dict__)
        else:
            logger.debug('loaded hash: {}'.format(block.hash))

    def create_genesis_block(self):
        # Manually construct a block with
        # index zero and arbitrary previous hash

        self.append(
            BritBlock(
                0,
                str(date.datetime.now().replace(microsecond=0)),
                INITIAL_DATA,
                "0"
            ),
            persist=True
        )

    def latest_block(self):
        """
        Return the most recent block.
        """

        return self[-1]

    def mine(self, nick, message):
        """
        hashes the current message with the pending transactions.

        If the hash begins with `DIFFICULTY` zero(s), it is considered mined and a
        britcoin is sent to the miner.
        """

        # Get the last block
        last_block = self.latest_block()

        proof = proof_of_conversation(last_block.hash_block(), message)

        if proof:

            # reward the miner
            self.pending_transactions.append(
                { u'from': u'network', u'to': nick, u'amount': 1 }
            )

            # Now we can gather the data needed
            # to create the new block
            new_block_data = {
                u'proof-of-work': unicode(proof),
                u'transactions': list(self.pending_transactions)
            }

            new_block_index = last_block.index + 1
            new_block_timestamp = str(date.datetime.now().replace(microsecond=0))

            # Empty pending transaction list
            self.pending_transactions[:] = []

            # Now create the new block!
            mined_block = BritBlock(
                new_block_index,
                new_block_timestamp,
                new_block_data,
                last_block.hash
            )

            self.append(mined_block, persist=True)

    def calculate_balances(self):

        balances = defaultdict(int)

        for block in self:
            for transaction in block.data.get('transactions', []):

                balances[transaction['to']] += transaction['amount']
                balances[transaction['from']] -= transaction['amount']

        return balances

    def stats(self):

        chain_balances = self.calculate_balances()
        coins_mined = abs(chain_balances['network'])


        blockchain_start = timestamp2datetime(self[0].timestamp)
        blockchain_end = timestamp2datetime(self[-1].timestamp)
        total_duration = blockchain_start - blockchain_end

        return u'{} britcoins | {} per britcoin'.format(
            coins_mined,
            humanize.naturaldelta(total_duration.total_seconds() / coins_mined)
        )


class BritCoinPlugin(Command):

    command = 'britcoin'
    help = "subcommands: stats, send, balances, balance"

    def __init__(self, *args, **kwargs):

        super(BritCoinPlugin, self).__init__(*args, **kwargs)

        self.blockchain = BritChain()

    def preprocess(self, client, channel, nick, message):

        if nick not in IGNORED and not message.startswith(CMD_PREFIX):
            self.blockchain.mine(nick, message)

        return channel, nick, message

    def run(self, client, channel, nick, message, cmd, args):
        """
        Subcommands:

        <bigjust> !britcoin stats
        <aineko> 23 britcoins, 3 hrs 57 minutes / 57 msgs per block

        <bigjust> !britcoin send brit 5
        <aineko> added bigjust -> brit (5 britcoins) to pending transactions

        <bigjust> !britcoin balances
        <aineko> bigjust: 2
        <aineko> brit: 5
        """

        if not args:
            return

        if args[0] == 'stats':
            output = self.blockchain.stats()

        if args[0] == 'send':
            output = u'bug bigjust to implement this.'

            if len(args) != 3:
                output = u'usage: send <nick> <number of britcoins>'

        if args[0] == 'balance':
            balances = self.blockchain.calculate_balances()
            nick_balance = balances.get(nick, 0)
            output = '{}, you have {} britcoin{}.'.format(
                nick,
                nick_balance,
                's' if nick_balance > 1 else '',
            )

        if args[0] == 'balances':
            for chain_nick, balance in self.blockchain.calculate_balances().iteritems():
                if chain_nick == 'network':
                    continue

                client.msg(channel, '{}: {}'.format(chain_nick, balance))
            return

        return output
