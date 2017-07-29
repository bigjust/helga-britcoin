import datetime as date
import hashlib

from helga import settings, log
from helga.plugins import preprocessor


logger = log.getLogger(__name__)


class BritcoinBlock(object):

    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.hash_block()

    def hash_block(self):
        sha = hashlib.sha256()
        sha.update(str(self.index) +
                   str(self.timestamp) +
                   str(self.data) +
                   str(self.previous_hash))
        return sha.hexdigest()

def create_genesis_block():
    # Manually construct a block with
    # index zero and arbitrary previous hash
    return BritcoinBlock(
        0, date.datetime.now(), "Genesis Block", "0"
    )

# Create the blockchain and add the genesis block
blockchain = [create_genesis_block()]
previous_block = blockchain[0]
pending_transactions = []

def proof_of_work(prev_hash, message):

    hasher = hashlib.sha256()
    hasher.update(prev_hash + message)
    hash_attempt = hasher.hexdigest()

    logger.debug('hash attempt: {}'.format(hash_attempt))

    if hash_attempt[0] == '0':
        return hash_attempt

def mine(nick, message):
    """
    hashes the current message with the pending transactions.

    If the hash begins with 1 zero, it is considered mined and a
    britcoin is sent to the miner.
    """

    # Get the last block
    last_block = blockchain[-1]

    proof = proof_of_work(last_block.hash_block(), message)

    if proof:

        # reward the miner
        pending_transactions.append(
            { "from": "network", "to": nick, "amount": 1 }
        )

        # Now we can gather the data needed
        # to create the new block
        new_block_data = {
            "proof-of-work": proof,
            "transactions": list(pending_transactions)
        }

        new_block_index = last_block.index + 1
        new_block_timestamp = this_timestamp = date.datetime.now()
        last_block_hash = last_block.hash

        # Empty transaction list
        this_nodes_transactions[:] = []

        # Now create the
        # new block!
        mined_block = BritcoinBlock(
            new_block_index,
            new_block_timestamp,
            new_block_data,
            last_block_hash
        )

        blockchain.append(mined_block)

        # Let the client know we mined a block

        return json.dumps({
            "index": new_block_index,
            "timestamp": str(new_block_timestamp),
            "data": new_block_data,
            "hash": last_block_hash
        }) + "\n"

@preprocessor
def britcoin(client, channel, nick, message):

    mine(nick, message)

    return channel, nick, message
