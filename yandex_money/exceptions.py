# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

__all__ = ['FormatError', 'ScopeError', 'TokenError', 'YandexPaymentError']


class APIException(Exception):
    pass


class FormatError(APIException):
    pass


class ScopeError(APIException):
    pass
        

class TokenError(APIException):
    pass


_errors = {
    'illegal_param_client_id': 'Недопустимое значение параметра client_id (не существует или заблокирован).'
                               'Дальнейшая работа приложения c данным client_id невозможна.',
    'contract_not_found': 'Отсутствует выставленный контракт с заданным request_id.',
    'not_enough_funds': 'Недостаточно средств на счете плательщика. '
                        'Необходимо пополнить счет и провести новый платеж.',
    'limit_exceeded': 'Превышен один из лимитов на операции:\n'
                    'на сумму операции для выданного токена авторизации;\n'
                    'сумму, операции за период времени для выданного токена авторизации;\n'
                    'ограничений Яндекс.Денег для различных видов операций.',
    'money_source_not_available': 'Запрошенный метод платежа (money_source) недоступен для данного платежа.',
    'illegal_param_csc': 'Отсутствует или указано недопустимое значение параметра csc.',
    'payment_refused': 'Магазин по какой-либо причине отказал в приеме платежа.',
    'authorization_reject': 'В авторизации платежа отказано. Возможные причины: истек срок действия банковской карты;\n'
                                        'банк-эмитент отклонил транзакцию по карте;\n'
                                        'превышен лимит для этого пользователя;\n'
                                        'транзакция с текущими параметрами запрещена для данного пользователя;\n'
                                        'пользователь не принял Соглашение об использовании сервиса «Яндекс.Деньги».',
    'account_blocked': 'Счет пользователя заблокирован. Для разблокировки счета необходимо отправить '
                       'пользователя по адресу, указанному в поле account_unblock_uri.',
    'illegal_param_ext_auth_success_uri': 'Отсутствует или указано недопустимое значение '
                                          'параметра ext_auth_success_uri.',
    'illegal_param_ext_auth_fail_uri': 'Отсутствует или указано недопустимое значение параметра ext_auth_fail_uri.',
    'illegal_param_protection_code': 'Отсутствует или имеет недопустимое значение параметр protection_code.',
    'illegal_param_operation_id': 'Отсутствует или имеет недопустимое значение параметр operation_id.'
                                  ' Перевод с таким ёoperation_id не существует или уже отвергнут.',
    'ext_action_required': 'В настоящее время приём переводов невозможен. Для получения возможности '
                           'приема переводов пользователю необходимо перейти на страницу по адресу '
                           'ext_action_uri и и следовать инструкции на данной странице.'
                           ' Это могут быть следующие действия:\n'
                        '* ввести идентификационные данные\n'
                        '* принять оферту\n'
                        '* выполнить иные действия согласно инструкциям на странице\n',
    'already_rejected': 'Перевод уже отвергнут.',
}


class YandexPaymentError(APIException):

    def __init__(self, error, *args, **kwargs):
        message = _errors.get(error, 'В авторизации платежа отказано.'
                                     ' Приложению следует провести новый платеж спустя некоторое время.')
        super(YandexPaymentError, self).__init__(message.encode('utf-8'), *args, **kwargs)