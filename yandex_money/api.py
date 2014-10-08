from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from six.moves.urllib.parse import urlencode
import requests

from . import exceptions


class BasePayment(object):
    MONEY_URL = "https://money.yandex.ru"
    SP_MONEY_URL = "https://sp-money.yandex.ru"

    @classmethod
    def send_request(cls, url, headers=None, body=None):
        if not headers:
            headers = {}
        headers['User-Agent'] = "Yandex.Money.SDK/Python";

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
        return result.json() if result.ok else result.raise_for_status()


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
    def __init__(self, instance_id):
        self.instance_id = instance_id

    @classmethod
    def get_instance_id(cls, client_id):
        return cls.send_request("/api/instance-id", body={
            "client_id": client_id
        })

    def request(self, options):
        options['instance_id'] = self.instance_id
        return self.send_request("/api/request-external-payment", body=options)

    def process(self, options):
        options['instance_id'] = self.instance_id
        return self.send_request("/api/process-external-payment", body=options)
