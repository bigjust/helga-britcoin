import datetime as date
import hashlib
import json
import smokesignal

from helga import settings, log
from helga.db import db
from helga.plugins import preprocessor


logger = log.getLogger(__name__)


class BritBlock(object):

    def __init__(self, index, timestamp, data, previous_hash):

        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):

        sha = hashlib.sha256()

        sha.update(
            str(self.index) +
            str(self.timestamp) +
            str(self.data) +
            str(self.previous_hash)
        )

        return sha.hexdigest()


class BritChain(list):

    def __init__(self):
        """
        Load blocks from mongodb. If none are found, create a genesis
        block.
        """

        super(BritChain, self).__init__()

        self.pending_transactions = []
        self.create_genesis_block()

    def __append__(self, block):
        """
        When blocks are added to the chain, add the block to mongodb.
        """

        super(BritChain, self).__append__(block)

        db.britcoin.insert(block.__dict__)

    def create_genesis_block(self):
        # Manually construct a block with
        # index zero and arbitrary previous hash

        self.append(BritBlock(
            0, date.datetime.now(), "Genesis Block", "0"
        ))

    def latest_block(self):
        """
        Return the most recent block.
        """

        return self[-1]

    def mine(self, nick, message):
        """
        hashes the current message with the pending transactions.

        If the hash begins with 1 zero, it is considered mined and a
        britcoin is sent to the miner.
        """

        # Get the last block
        last_block = self.latest_block()

        proof = proof_of_work(last_block.hash_block(), message)

        if proof:

            # reward the miner
            self.pending_transactions.append(
                { "from": "network", "to": nick, "amount": 1 }
            )

            # Now we can gather the data needed
            # to create the new block
            new_block_data = {
                "proof-of-work": proof,
                "transactions": list(self.pending_transactions)
            }

            new_block_index = last_block.index + 1
            new_block_timestamp = this_timestamp = date.datetime.now()
            last_block_hash = last_block.hash

            # Empty pending transaction list
            self.pending_transactions[:] = []

            # Now create the new block!
            mined_block = BritBlock(
                new_block_index,
                new_block_timestamp,
                new_block_data,
                last_block_hash
            )

            self.append(mined_block)

# Create the blockchain and add the genesis block
blockchain = BritChain()

def work(prev_hash, message):
    hasher = hashlib.sha256()
    hasher.update(prev_hash + message)
    hash_attempt = hasher.hexdigest()

    return hash_attempt

def proof_of_work(prev_hash, message):
    """
    r/AnAttemptWasMade
    """

    attempt = work(prev_hash, message)

    if attempt.startswith('00'):
        return attempt

@preprocessor
def britcoin(client, channel, nick, message):
    blockchain.mine(nick, message)
    return channel, nick, message

@smokesignal.on('join')
def join_channel(client, channel):
    pass
