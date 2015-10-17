
import json
import decimal

from fabric.api import run
from fabric.context_managers import settings

from gcointest.exceptions import JSONRPCException, CoreException
from gcointest import config


class AuthServiceProxy(object):

    def __init__(self, host, exception_wrapper=None):
        self.host = host
        self._exception_wrapper = exception_wrapper

    def __getattr__(self, name):
        return RPCMethod(name, self)

    def _raise_exception(self, error):
        if self._exception_wrapper is None:
            raise JSONRPCException(error)
        else:
            raise self._exception_wrapper(error)

    def start(self):
        command = ('$HOME/gcoin/src/bitcoind -gcoin -daemon -reindex -logip -debug'
                  ' -port={0} -rpcport={1} -rpcthreads={2}'.format(config.port, config.rpcport, config.rpcthreads))
        resp = run(command)

        if resp.failed:
            raise CoreException("bitcoind launch failed", self.host)

    def reset(self):
        command = ("rm -rf $HOME/.bitcoin/gcoin")
        with settings(warn_only=True):
            return run(command)


class RPCMethod(object):

    def __init__(self, name, service_proxy):
        self._method_name = name
        self._service_proxy  = service_proxy

    def __call__(self, *args, **kwargs):
        warn_only = kwargs.pop("warn_only", False)

        parameter = ' '.join(str(i) for i in args)
        command = "$HOME/gcoin/src/bitcoin-cli -gcoin {method} {param}".format(method=self._method_name,
                                                                               param = parameter)
        with settings(warn_only=True):
            resp = run(command)

        if resp.find("error") != -1 and not warn_only:
            resp = resp.split("error: ")[1]

            if resp.find("Loading wallet...") != -1 or resp.find("Loading block index...") != -1:
                raise CoreException(resp, self._service_proxy.host)

            try:
                self._service_proxy._raise_exception(json.loads(resp))
            except ValueError:
                raise CoreException(resp, self._service_proxy.host)

        try:
            resp = json.loads(resp, parse_float=decimal.Decimal)
        except ValueError:
            pass
        return resp

    def __repr__(self):
        return '<RPCMethod object "{name}">'.format(name=self._method_name)

