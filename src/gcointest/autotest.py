#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import random

from fabric.api import env, hosts, roles, parallel
from fabric.tasks import execute
from fabric.contrib.console import confirm
from fabric.colors import red, green, yellow, cyan

from gcointest.roles import BaseRole, Alliance
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

    def _random_choose_an_address(self, role):
        host = random.choice(env.roledefs[role])
        address = random.choice(self.collect_addresses[host]['wallet'])

        return address

    def _random_choose_an_unused_color(self):
        """
        License Transfer is forbidden, which may cause error.
        """
        while True:
            if len(self.applied_colors.keys()) == config.NUM_COLORS:
                raise BaseTestException(env.host,
                                        "color has been run out")

            color = random.randint(2, config.NUM_COLORS)
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

                # send lot of color1 coint to other alliance
                alliance.send_coins(alliance.address,
                                    self.collect_addresses[host]['default'],
                                    1000000000/num_alliance, 1)
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

        return alliance.apply_license_1(alliance.address, 10000000000)

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
    def random_create_payment(self):
        pass


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

    print red("-- RUNNING AUTOTEST --")
    # Random apply licenses
    for i in xrange(config.TEST_RUN_ITER):
        ret = execute(autotest.random_apply_license)
        for host, result in ret.iteritems():
            autotest.applied_colors[result.keys()[0]] = result.values()[0]

    # Random create payments
    # TODO

    print green("-- FINISHED --")
    print autotest.applied_colors

