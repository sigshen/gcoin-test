
roledefs = {
    'alliance': ['core1.diqi.us', 'core2.diqi.us'],
    'issuer': ['core1.diqi.us', 'core2.diqi.us'],
    'others': ['core1.diqi.us', 'core2.diqi.us'],
    'monitor': [],
}

remote_user = 'sig'
ssh_key_filename = '/Users/sig/.ssh/id_rsa'

# bitcoind configuration
port = 55888
rpcport = 12345
rpcthreads = 20

NUM_ADDRESS_PER_NODE = 30
NUM_COLOR = 1000 # num of color you want to use
MAX_NUM_MEMBERS_PER_ISSUER = 10
MAX_TRANSACTION_NUM_ALLOWED_PER_MEMBER_PER_COLOR = 30
MAX_AMOUNT_PER_PAYMENT = 300
NUM_ATTEMPT_CREATE_PAYMENT = 100000

INITIAL_AMOUNT_PER_ISSUER = 10**9 # should can be 10^10
MAX_COIN = 10**10
MIN_ACTIVATION_BTC = 1
LICENSE_MATURITY = 10
COINBASE_MATURITY = 10

FAKE_LICENSE_HEX_STRING = "72110100046e616d650364657304616464720100000000000000000000000004616464720000000001046c696e6b0000000000000000000000000000000000000000000000000000000000000000"

"""
FAKE_LICENSE_INFO = {
    "version": 1,
    "name": "",
    "description": "description",
    "issuer": "",
    "divisibility": True,
    "fee_type": "fixed",
    "fee_rate": 0.0,
    "fee_collector": "",
    "mint_schedule": "free",
    "member_control": True,
    "metadata_link": "hyperlink",
    "metadata_hash": "hash"
}
"""

