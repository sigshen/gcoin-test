
import time

from fabric.api import env, hosts
from fabric.colors import yellow, cyan
from fabric.tasks import execute

from gcointest.exceptions import wrap_exception
from gcointest.proxy import AuthServiceProxy, RPCMethod
from gcointest.decorators import severaltry
from gcointest.exceptions import CoreException, WalletError, InvalidAddressOrKey
from gcointest import config


env.roledefs = config.roledefs
env.hosts = list(set(env.roledefs['alliance'] + env.roledefs['issuer'] + env.roledefs['others']))

def _activate_address_by_issuer_1(bitcoinaddress, issuer_1_address):
    issuer = Issuer(env.host, issuer_1_address, 1)

    return issuer.activate(bitcoinaddress)

class BaseRole(object):
    """
    An abstract common interface for both `Alliance` and `Issuer`.
    """

    def __init__(self, host):
        """
        Create a new bitcoin server connection.
        """
        self.host = host
        self.proxy = AuthServiceProxy(host, exception_wrapper=wrap_exception)

    def _wait_for_maturity(self, tx_hash, maturity, timeout=300, sleep_interval=1):
        loop_cnt = (timeout/sleep_interval) + 1
        while loop_cnt > 0:
            try:
                result = self.getrawtransaction(tx_hash)
            except InvalidAddressOrKey as e:
                # Skip No information available about transaction rpc error
                print cyan(type(e))
                time.sleep(1)
                loop_cnt -= 1
                continue

            if result.has_key('confirmations') and result['confirmations'] > maturity:
                return tx_hash
            time.sleep(1)
            loop_cnt -= 1

    def getlicenseinfo(self):
        return self.proxy.getlicenseinfo()

    def getrawtransaction(self, txid, verbose=True):
        if verbose:
            return self.proxy.getrawtransaction(txid, 1)
        return self.proxy.getrawtransaction(txid, 0)

    def getblockcount(self):
        return self.proxy.getblockcount()

    def send_coins(self, frombitcoinaddress, tobitcoinaddress, amount, color):
        tx_hash = self.proxy.sendfrom(frombitcoinaddress,
                                      tobitcoinaddress, amount, color)
        return self._wait_for_maturity(tx_hash, 1)

    def keypoolrefill(self, num):
        return self.proxy.keypoolrefill(num)

    @severaltry(time_out=300, sleep_interval=1)
    def getfixedaddress(self):
        return self.proxy.getfixedaddress()

    def listwalletaddress(self, num, refill=True):
        if refill:
            self.keypoolrefill(num)
        return self.proxy.listwalletaddress("-p", num)

    def start(self):
        return self.proxy.start()

    def stop(self):
        return self.proxy.stop()

    def reset_and_restart(self):
        self.proxy.stop(warn_only=True)
        self.proxy.reset()

        return self.start()

    def restart(self):
        self.proxy.stop(warn_only=True)
        return self.proxy.start()

    def addnode(self, host, port):
        address = host + ":" + str(port)

        # Skip rpc error: Node already added
        self.proxy.addnode(address, 'add', warn_only=True)
        self.proxy.addnode(address, 'onetry')


class Issuer(BaseRole):

    def __init__(self, host, bitcoinaddress, color):
        super(Issuer, self).__init__(host)
        self.address = bitcoinaddress
        self.color = color

    def mint(self, amount, maturity):
        pass

    def create_payment(self, tobitcoinaddress, amount):
        return self.send_coins(self.address,
                               tobitcoinaddress,
                               amount, self.color)

    def activate(self, bitcoinaddress):
        return self.send_coins(self.address,
                               bitcoinaddress,
                               config.MIN_ACTIVATION_BTC,
                               self.color)


class Alliance(BaseRole):

    def __init__(self, host, bitcoinaddress):
        super(Alliance, self).__init__(host)
        self.address = bitcoinaddress

    def mint_0(self, amount):
        for i in xrange(amount):
            tx_hash = self.proxy.mint(amount, 0)

        return self._wait_for_maturity(tx_hash, config.COINBASE_MATURITY)

    def start_mining(self):
        return self.proxy.setgenerate("true")

    def vote(self, bitcoinaddress):
        return self.proxy.sendvotetoaddress(bitcoinaddress)

    def apply_license_1(self, bitcoinaddress, default_amount):
        """
        Should be used only for head alliance.
        """
        color = 1
        self.mint_0(1)

        tx_hash_1 = self.proxy.sendlicensetoaddress(bitcoinaddress, color)
        self._wait_for_maturity(tx_hash_1, config.LICENSE_MATURITY)

        tx_hash_2 = self.proxy.mint(default_amount, color)
        return self._wait_for_maturity(tx_hash_2, config.COINBASE_MATURITY)

    def apply_license_normal(self, bitcoinaddress, color_id, issuer_1_address):
        self.mint_0(1)
        try:
            tx_hash = self.proxy.sendlicensetoaddress(bitcoinaddress, color_id)
        except (WalletError, CoreException) as e:
            # Skip possible license transfer or other errors
            print cyan(e)
            return None

        # TODO: Refactor this
        # activate address so that we can send color 1 coin to it
        execute(_activate_address_by_issuer_1, bitcoinaddress, issuer_1_address,
                                              hosts=[env.roledefs['alliance'][0],])

        self.send_coins(self.address,
                        bitcoinaddress,
                        config.MAX_TRANSACTION_NUM_ALLOWED_PER_ISSUER, 1)
        return self._wait_for_maturity(tx_hash, config.LICENSE_MATURITY)

    def is_alliance(self, tx_hash=None, maturity=False):

        # Quick answer for this case
        if not maturity:
            if self.address in self.proxy.getmemberlist()['member_list']:
                return True
            else:
                return False

