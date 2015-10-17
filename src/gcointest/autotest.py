#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random

from fabric.api import env, hosts, roles, parallel
from fabric.tasks import execute
from fabric.contrib.console import confirm
from fabric.colors import red, green, yellow, cyan

from gcointest.roles import BaseRole, Alliance, Issuer
from gcointest.exceptions import BaseTestException
from gcointest import config

env.roledefs = config.roledefs
env.user = config.remote_user
env.key_filename = config.ssh_key_filename
env.hosts = list(set(env.roledefs['alliance'] + env.roledefs['issuer'] + env.roledefs['others']))

RESET_BLOCKCHAIN = True


class BaseTest(object):

    def __init__(self):
        self.collect_addresses = execute(self.setUp)

    @parallel
    def setUp(self):
        """
        Method called to prepare the test fixture.

        1. Start Bitcoin Core Daemon and get a default Bitcoin address.
        2. Attempt to try a connection to a node once in our host list.
        3. Get fixed(default) and some normal addresses in core wallet.
        """
        result = {}

        role = BaseRole(env.host)
        if RESET_BLOCKCHAIN:
            role.reset_and_restart()
        else:
            role.start()

        result['default'] = role.getfixedaddress()

        # Try a connection with each other
        for host in env.hosts:
            if host == env.host:
                continue
            role.addnode(host, config.port)

        result['wallet'] = role.listwalletaddress(config.NUM_ADDRESS_PER_NODE)
        return result


class AutoTest(BaseTest):

    def __init__(self):
        super(AutoTest, self).__init__()
        self.applied_colors = {}
        self.applied_members = {}

    def _random_choose_an_address(self, role):
        host = random.choice(env.roledefs[role])
        address = random.choice(self.collect_addresses[host]['wallet'])

        return address

    def _random_choose_an_unused_color(self):
        """
        License Transfer is forbidden, which may cause error.
        """
        while True:
            if len(self.applied_colors.keys()) == config.NUM_COLOR:
                raise BaseTestException(env.host, "color has been run out")

            color = random.randint(2, config.NUM_COLOR)
            if color not in self.applied_colors.keys():
                return color

    @roles('alliance')
    @parallel
    def start_all_miners(self):
        alliance = Alliance(env.host, self.collect_addresses[env.host]['default'])

        return alliance.start_mining()

    @roles('alliance')
    @parallel
    def setup_head_alliance(self):
        alliance = Alliance(env.host, self.collect_addresses[env.host]['default'])

        if env.host == env.roledefs['alliance'][0]:
            alliance.start_mining()
        else:
            # To ensure that other alliance acknowledge the first alliance
            acknowledged = False
            while not acknowledged:
                if alliance.getblockcount() > 0:
                    acknowledged = True

    @roles('alliance')
    @parallel
    def vote_and_send_color1_coins(self):
        alliance = Alliance(env.host, self.collect_addresses[env.host]['default'])

        if env.host == env.roledefs['alliance'][0]:
            num_alliance = len(env.roledefs['alliance'][1:])
            alliance.mint_0(num_alliance)
            for host in env.roledefs['alliance'][1:]:
                alliance.vote(self.collect_addresses[host]['default'])

                '''
                # send lot of color 1 coin to other alliance (for the use of activate member)
                amount_1 = config.NUM_ISSUER_PER_ALLIANCE * config.NUM_MEMBERS_PER_ISSUER
                alliance.send_coins(alliance.address,
                                    self.collect_addresses[host]['default'],
                                    amount_1, 1)
                '''
        else:
            while not alliance.is_alliance():
                time.sleep(1)
            my_pos = env.roledefs['alliance'].index(env.host)
            for host in env.roledefs['alliance'][my_pos+1:]:
                alliance.vote(self.collect_addresses[host]['default'])

    @hosts(env.roledefs['alliance'][0])
    def apply_license_1(self):
        """
        Let head alliance own the license 1.
        """
        color = 1

        alliance = Alliance(env.host, self.collect_addresses[env.host]['default'])
        self.applied_colors[color] = alliance.address

        return alliance.apply_license_1(alliance.address, config.MAX_COIN)

    @roles('alliance')
    @parallel
    def random_apply_license(self):
        result = {}

        alliance = Alliance(env.host, self.collect_addresses[env.host]['default'])
        address = self._random_choose_an_address('issuer')
        color = self._random_choose_an_unused_color()

        alliance.apply_license_normal(address, color, self.applied_colors[1])
        result = {color: address}

        return result

    @roles('issuer')
    @parallel
    def mint_all_i_can_mint_after_become_issuer(self):
        role = BaseRole(env.host)
        licenseinfo = role.getlicenseinfo()
        for color, info in licenseinfo.iteritems():
            if int(color) == 1:
                # already minted in apply_license_1()
                # skip this case otherwise coins may overflow
                continue
            issuer = Issuer(env.host, info['address'], color)
            # TODO: if mint MAX_COINS = 10^10
            # sendfrom rpc error: The transaction was rejected  will happen
            issuer.mint(config.INITIAL_AMOUNT_PER_ISSUER)

    @roles('issuer')
    @parallel
    def random_apply_member(self):
        result = {}

        role = BaseRole(env.host)
        licenseinfo = role.getlicenseinfo()
        for color, info in licenseinfo.iteritems():
            if int(color) == 1:
                # for the use of fee
                continue

            members = []
            issuer = Issuer(env.host, info['address'], color)
            for idx in xrange(config.MAX_NUM_MEMBERS_PER_ISSUER):
                member_address = self._random_choose_an_address('others')
                if member_address in members:
                    continue
                issuer.activate(member_address, config.INITIAL_AMOUNT_PER_ISSUER / config.MAX_NUM_MEMBERS_PER_ISSUER)
                members.append(member_address)

            result[color] = members

        return result

    @roles('issuer')
    def supply_sufficient_fee_for_members(self):
        # head alliance must be issuer 1
        if env.host != env.roledefs['issuer'][0]:
            return

        issuer = Issuer(env.host, self.applied_colors[1], 1)
        for color, addresses in self.applied_members.iteritems():
            for address in addresses:
                issuer.activate(address, config.MAX_TRANSACTION_NUM_ALLOWED_PER_MEMBER_PER_COLOR)

    def make_plan_random_create_payment(self):
        color = random.choice(self.applied_members.keys())
        from_address, to_address = random.sample(self.applied_members[color], 2)

        for host in self.collect_addresses.keys():
            if from_address in self.collect_addresses[host]['wallet']:
                return host, from_address, to_address, color

    def create_payment(self, from_address, to_address, amount, color):
        role = BaseRole(env.host)
        balances = role.getaddressbalance(from_address)
        if not balances.has_key(str(color)) or not balances.has_key("1") or int(balances[color]) < amount:
            # insufficient funds
            return

        role.send_coins(from_address, to_address, amount, color)
        msg = "{from_addr} send {amount} of color: {color} TO {to_addr}".format(from_addr=from_address,
                                                                                amount=amount,
                                                                                color=color,
                                                                                to_addr=to_address)
        print green(msg)


if __name__ == '__main__':
    if not confirm("Reset BlockChain? (y)"):
        RESET_BLOCKCHAIN = False

    print red("-- SETTING UP CONNECTION --")
    autotest = AutoTest()

    print red("-- SETTING UP ALLIANCE --")
    if RESET_BLOCKCHAIN:
        execute(autotest.setup_head_alliance)
        execute(autotest.apply_license_1)
        execute(autotest.vote_and_send_color1_coins)
    execute(autotest.start_all_miners)

    print red("-- RANDOM APPLY LICENSE --")
    for i in xrange(3):
        ret = execute(autotest.random_apply_license)
        for host, result in ret.iteritems():
            autotest.applied_colors[result.keys()[0]] = result.values()[0]

    print red("-- MINTING --")
    execute(autotest.mint_all_i_can_mint_after_become_issuer)

    print red("-- RANDOM APPLY MEMBER --")
    ret = execute(autotest.random_apply_member)
    for host, result in ret.iteritems():
        for color, members in result.iteritems():
            autotest.applied_members[color] = members

    print red("-- SUPPLY SUFFICIENT FEE FOR MEMBER --")
    execute(autotest.supply_sufficient_fee_for_members)

    print green(autotest.applied_members)

    print red("-- RANDOM CREATE PAYMENT --")
    # TODO: multiple iteration
    for indx in xrange(config.NUM_ATTEMPT_CREATE_PAYMENT):
        host, from_address, to_address, color = autotest.make_plan_random_create_payment()
        amount = random.randint(1, config.MAX_AMOUNT_PER_PAYMENT)
        execute(autotest.create_payment, from_address, to_address, amount, color, hosts=[host,])

    print red("-- FINISHED --")

