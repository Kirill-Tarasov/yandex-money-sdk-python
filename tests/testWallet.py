from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import unittest
import json
import re
import responses
from six.moves.urllib.parse import parse_qsl

from yandex_money.api import Wallet, ExternalPayment
from yandex_money import exceptions
from constants import CLIENT_ID, ACCESS_TOKEN


class WalletTestSuite(unittest.TestCase):
    def setUp(self):
        super(WalletTestSuite, self).setUp()
        self.api = Wallet(ACCESS_TOKEN)

    def assert_auth_header_present(self):
        pass

    def testAccountInfo(self):
        response = self.api.account_info()
        self.assert_auth_header_present()

    def testGetAuxToken(self):
        token = "some_aux_token"

        response = self.api.get_aux_token(["account-info", "operation-history"])

        self.assertIn('aux_token', response)

    def testOperationHistory(self):
        options = {"records": 3}
        response = self.api.operation_history(options)

    def testOperationDetails(self):
        pass

    def testRequestPayment(self):
        options = {
            "pattern_id": "p2p",
            "to": "410011161616877",
            "amount_due": "0.02",
            "comment": "test payment comment from yandex-money-python",
            "message": "test payment message from yandex-money-python",
            "label": "testPayment",
            "test_payment": True,
            "test_result": "success"
        }

        response = self.api.request_payment(options)
        self.assertEqual(response['status'], 'success')

    def testResponsePayment(self):
        options = {
            "request_id": "test-p2p",
            "test_payment": True,
            "test_result": "success"
        }

        response = self.api.process_payment(options)
        self.assertEqual(response['status'], 'success')

    def testIncomingTransferAccept(self):
        #self.addResponse("incoming-transfer-accept", {"status": "success"})
        operation_id = "some id"
        protection_code = "some code"  # TODO: test when it's None

        response = self.api.incoming_transfer_accept(
            operation_id=operation_id,
            protection_code=protection_code
        )
        self.assertEqual(response['status'], "refused")

    def testIncomingTransferReject(self):
        #self.addResponse("incoming-transfer-reject", {"status": "success"})
        operation_id = "some operatoin id"
        response = self.api.incoming_transfer_reject(
            operation_id=operation_id,
        )

    def testObtainTokenUrl(self):
        client_id = "client-id"
        url = Wallet.build_obtain_token_url(
            "client-id",
            "http://localhost/redirect",
            ["account-info", "operation_history"]
        )
        # TODO: check url

    def testGetAccessToken(self):
        options = {
            "code": "code",
            "client_id": "client_id",
            "grant_type": "authorization_code",
            "redirect_uri": "redirect_uri",
            "client_secret": "client_secret"
        }
        response = Wallet.get_access_token(
            code=options["code"],
            client_id=options["client_id"],
            redirect_uri=options["redirect_uri"],
            client_secret=options["client_secret"]
        )
        self.assertEqual(response['error'], 'unauthorized_client')


class TestExternalPayment(unittest.TestCase):
    client_id = '1'

    @classmethod
    def request_callback(cls, request):
        payload = dict(parse_qsl(request.body))
        success = payload['client_id'] == cls.client_id
        resp_body = {'status': 'success' if success else 'refused'}
        if success:
            resp_body['instance_id'] = '123'
        else:
            resp_body['error'] = 'illegal_param_client_id'
        return 200, {}, json.dumps(resp_body)

    def setUp(self):
        self.api = ExternalPayment(self.client_id)
        responses.add_callback(
            responses.POST, re.compile('https?://.*/api/instance-id'),
            callback=self.request_callback,
            content_type='application/json',
        )

    @responses.activate
    def test_invalid_client_id(self):
        api = ExternalPayment(client_id=self.client_id+'some_data')

        with self.assertRaises(exceptions.YandexPaymentError) as context:
            api.instance_id
        self.assertEqual(exceptions._errors['illegal_param_client_id'].encode('utf-8'), str(context.exception))
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_instance_id(self):
        self.assertEqual(self.api.instance_id, '123')
        self.assertEqual(len(responses.calls), 1)

        api2 = ExternalPayment(client_id=self.client_id)

        self.assertEqual(api2.instance_id, '123')
        self.assertEqual(len(responses.calls), 1)

    @responses.activate
    def test_request(self):
        def callback(request):
            payload = dict(parse_qsl(request.body))
            success = all(i in payload for i in ['amount', 'to', 'message', 'instance_id'])
            if success:
                return 200, {}, json.dumps({'status': 'success', 'request_id': 1, 'contract_amount': payload['amount']})
            return 200, {}, json.dumps({'status': 'refused', 'error': 'illegal_params'})

        responses.add_callback(
            responses.POST, re.compile('https?://.*/api/request-external-payment'),
            callback=callback,
            content_type='application/json',
        )

        resp = self.api.request({'amount': 100, 'to': 'test', 'message': 'message'})
        self.assertEqual(resp.request_id, 1)
        self.assertEqual(int(resp.contract_amount), 100)

        with self.assertRaises(exceptions.YandexPaymentError) as context:
            resp = self.api.request({'message': 'message'})

        self.assertEqual(exceptions._errors['illegal_params'].encode('utf-8'), str(context.exception))
        self.assertEqual(len(responses.calls), 3)

    @responses.activate
    def test_process(self):
        def callback(request):
            payload = dict(parse_qsl(request.body))
            success = True
            if payload['request_id'] != 1:
                success = False
            success = all(i in payload for i in ['ext_auth_success_uri', 'ext_auth_fail_uri',
                                                 'request_token', 'instance_id'])
            if success:
                return 200, {}, json.dumps({'status': 'success', 'invoice_id': '0'})
            return 200, {}, json.dumps({'status': 'refused', 'error': 'illegal_params'})

        responses.add_callback(
            responses.POST, re.compile('https?://.*/api/process-external-payment'),
            callback=callback,
            content_type='application/json',
        )

        resp = self.api.process({'request_id': 1,
                                 'ext_auth_success_uri': 'test',
                                 'ext_auth_fail_uri': 'test_fail',
                                 'request_token': 'request_token',
                                 'instance_id': '123',
                                 })
        self.assertEqual(resp.status, 'success')
        self.assertEqual(resp.invoice_id, '0')

        self.assertEqual(len(responses.calls), 2)

    def tearDown(self):
        self.api.zero_cache()