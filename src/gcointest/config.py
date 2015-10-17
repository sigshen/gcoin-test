
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

