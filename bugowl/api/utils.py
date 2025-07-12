import logging
import time
from enum import Enum

import requests
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(settings.ENV)


class HttpMethod(Enum):
	GET = 1
	POST = 2
	PATCH = 3
	PUT = 4
	DELETE = 5


class JobStatusEnum(str, Enum):
	SCHEDULED = 'Scheduled'
	QUEUED = 'Queued'
	RUNNING = 'Running'
	CANCELED = 'Canceled'
	PASS_ = 'Pass'
	FAILED = 'Failed'

	@classmethod
	def choices(cls):
		return [(role.value, role.value.title()) for role in cls]


class Browser(str, Enum):
	CHROME = 'chrome'
	FIREFOX = 'firefox'
	SAFARI = 'safari'
	EDGE = 'edge'

	@classmethod
	def choices(cls):
		return [(browser.value, browser.value.title()) for browser in cls]


class HttpUtils:
	@staticmethod
	def invoke_http_request_inner(
		method,
		url,
		headers=None,
		payload=None,
		json=None,
		files=None,
		params=None,
		skip_ssl_check=False,
	):
		data = json
		if payload:
			data = payload
		header_param = ''
		for h in headers:
			header_param = header_param + f" --header '{h}:{headers[h]}' "
		curl_command = f"curl --location  --request {method.name} {url} {header_param} --data '{data}' "
		logger.info(curl_command)
		if method == HttpMethod.GET:
			response = requests.get(
				url,
				headers=headers,
				files=files,
				params=params,
				verify=not skip_ssl_check,
			)
		elif method == HttpMethod.POST:
			response = requests.post(
				url,
				headers=headers,
				data=payload,
				json=json,
				files=files,
				verify=not skip_ssl_check,
			)
		elif method == HttpMethod.PUT:
			response = requests.put(
				url,
				headers=headers,
				data=payload,
				files=files,
				verify=not skip_ssl_check,
			)
		elif method == HttpMethod.PATCH:
			response = requests.patch(
				url,
				headers=headers,
				data=payload,
				files=files,
				verify=not skip_ssl_check,
			)
		elif method == HttpMethod.DELETE:
			response = requests.delete(url, headers=headers, files=files, verify=not skip_ssl_check)
		else:
			logger.error('Invalid HTTP method', exc_info=True)
		return response

	@staticmethod
	@shared_task()
	def make_http_call(
		method,
		url,
		headers=None,
		payload=None,
		json=None,
		files=None,
		params=None,
		headers_required=True,
		skip_ssl_check=False,
	):
		TRIM_LEN = 2000
		response = {}
		try:
			if not files and headers_required:
				if not headers:
					headers = {}
				if 'Content-Type' not in headers:
					headers['Content-Type'] = 'application/json'
				headers['Accept'] = '*/*'
			log_msg = f'CALLING API: {method} - {url}  headers: {headers}, payload: {payload} , json: {json}'
			logger.info(log_msg[0:TRIM_LEN])
			response = HttpUtils.invoke_http_request_inner(method, url, headers, payload, json, files, params, skip_ssl_check)
			if response.status_code >= 500:
				logger.error(f'Got server error of {response.status_code}, retrying again in 5 seconds', exc_info=True)
				time.sleep(5)
				response = HttpUtils.invoke_http_request_inner(method, url, headers, payload, json, files, params, skip_ssl_check)
			if (
				response.status_code < 200 or response.status_code > 299 and 'slack' not in url
			):  # if slack call fails it can go in infinite loop
				is_internal_call = response.status_code == 401 and 'baya.biz' in url
				if not is_internal_call:
					# With tracback prefix it logs to Slack channel
					logger.error(
						f'HTTP call failed: {response.status_code} {response.content} | {method} - {url}  headers: {headers}, payload: {payload} , json: {json}',
						exc_info=True,
					)
			logger.info(response)
			logger.info(response.content[:TRIM_LEN])
		except Exception as e:
			logger.error(f'Unexpected error during HTTP request: {str(e)}', exc_info=True)
			if 'slack' not in url:  # If slack call fails due to some formatting issue, it goes into infinite loop
				logger.error('API Call failed: ', exc_info=True)
		return response
