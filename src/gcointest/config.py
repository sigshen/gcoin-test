# XXX: roledefs['others'] should not be empty if you set ALLIANCE_FOCUS_ON_MINING

roledefs = {
    'alliance': ['core1.diqi.us', 'core2.diqi.us'],
    'issuer': ['core1.diqi.us', 'core2.diqi.us'],
    'others': [],
    'monitor': [],
}

remote_user = 'sig'
ssh_key_filename = '/Users/sig/.ssh/id_rsa'

# bitcoind configuration
port = 55888
rpcport = 12345
rpcthreads = 20

TEST_RUN_ITER = 50
NUM_ADDRESS_PER_NODE = 10
NUM_COLORS = 10 # num of color you want to use
MAX_TRANSACTION_NUM_ALLOWED_PER_ISSUER = 10000


MIN_ACTIVATION_BTC = 1
LICENSE_MATURITY = 10
COINBASE_MATURITY = 10

