from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from copy import copy

from six.moves.urllib.parse import urlencode
import requests

from . import exceptions


__all__ = ['Wallet', 'ExternalPayment']


class BasePayment(object):
    MONEY_URL = "https://money.yandex.ru"
    SP_MONEY_URL = "https://sp-money.yandex.ru"

    @classmethod
    def send_request(cls, url, headers=None, body=None):
        if not headers:
            headers = {}
        headers['User-Agent'] = "Yandex.Money.SDK/Python"

        if not body:
            body = {}
        full_url = cls.MONEY_URL + url
        return cls.process_result(
            requests.post(full_url, headers=headers, data=body)
        )

    @classmethod
    def _handler_errors(cls, result):
        if result.status_code == 400:
            raise exceptions.FormatError
        elif result.status_code == 401:
            raise exceptions.TokenError
        elif result.status_code == 403:
            raise exceptions.ScopeError

    @classmethod
    def process_result(cls, result):
        cls._handler_errors(result)
        return _AttribDict(result.json()) if result.ok else result.raise_for_status()


class Wallet(BasePayment):
    def __init__(self, access_token):
        self.access_token = access_token

    def _send_authenticated_request(self, url, options=None):
        return self.send_request(
            url, {"Authorization": "Bearer {}".format(self.access_token)}, options)

    def account_info(self):
        return self._send_authenticated_request("/api/account-info")

    def get_aux_token(self, scope):
        return self._send_authenticated_request("/api/token-aux", {
            "scope": ' '.join(scope)
        })

    def operation_history(self, options):
        return self._send_authenticated_request("/api/operation-history",
                                                options)

    def request_payment(self, options):
        return self._send_authenticated_request("/api/request-payment",
                                                options)

    def process_payment(self, options):
        return self._send_authenticated_request("/api/process-payment",
                                                options)

    def incoming_transfer_accept(self, operation_id, protection_code=None):
        return self._send_authenticated_request(
            "/api/incoming-transfer-accept", {
                "operation_id": operation_id,
                "protection_code": protection_code
            })

    def incoming_transfer_reject(self, operation_id):
        return self._send_authenticated_request("/api/incoming-transfer-reject",
                                                {"operation_id": operation_id})

    @classmethod
    def build_obtain_token_url(cls, client_id, redirect_uri, scope):
        params = urlencode({"client_id": client_id,
                            "redirect_uri": redirect_uri,
                            "scope": " ".join(scope)})
        return "{}/oauth/authorize?{}".format(cls.SP_MONEY_URL, params)

    @classmethod
    def get_access_token(cls, client_id, code, redirect_uri,
                         client_secret=None):
        full_url = cls.SP_MONEY_URL + "/oauth/token"
        return cls.process_result(requests.post(full_url, data={
            "code": code,
            "client_id": client_id,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "client_secret": client_secret
        }))

    @classmethod
    def revoke_token(cls, token, revoke_all=False):
        return cls.send_request("/api/revoke", body={
            "revoke-all": revoke_all
        }, headers={"Authorization": "Bearer {}".format(token)})


class ExternalPayment(BasePayment):
    __cache = {}  # cross instances cache

    def __init__(self, client_id=None, instance_id=None):
        if (client_id or instance_id) is None:
            raise TypeError('instance required instance_id or client_id argument')
        self.client_id, self.__instance_id = client_id, instance_id

    @property
    def instance_id(self):
        if self.__instance_id is not None:
            if callable(self.__instance_id):
                self.__instance_id = self.__instance_id()
            return self.__instance_id
        if 'instance_id' not in self.__cache:
            resp = self.send_request("/api/instance-id", body={
                "client_id": self.client_id
            })
            self.__cache['instance_id'] = resp['instance_id'] if resp['status'] == 'success' else None
        return self.__cache['instance_id']

    def request(self, options):
        options = copy(options)
        options['instance_id'] = self.instance_id
        return self.send_request("/api/request-external-payment", body=options)

    def process(self, options):
        options = copy(options)
        options['instance_id'] = self.instance_id
        return self.send_request("/api/process-external-payment", body=options)



    @classmethod
    def zero_cache(cls):
        cls.__cache = {}

    @classmethod
    def _handler_errors(cls, result):
        super(ExternalPayment, cls)._handler_errors(result)
        result = result.json()
        if result['status'] == 'refused':
            raise exceptions.YandexPaymentError(result['error'])


class _AttribDict(dict):
    def __getattribute__(self, name):
        if name in ['status', 'error', 'acs_uri', 'acs_params', 'money_source',
                    'next_retry', 'invoice_id', 'instance_id', 'request_id',
                    'contract_amount', 'title', 'balance', 'account', 'currency',
                    'account_status', 'account_type', 'avatar', 'services_additional',
                    'cards_linked', 'balance_details', 'operations', 'next_record']:
            return super(_AttribDict, self).__getitem__(name)
        return super(_AttribDict, self).__getattribute__(name)