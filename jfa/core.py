#!/usr/bin/env python3
# coding=utf-8

import base64
import json
import os
import re
import urllib.parse as urlparse
import urllib.request as urlrequest
from gzip import GzipFile
from io import BytesIO
from typing import Optional, Sequence

from jfa.types import Result

# Unique identifier for the workflow bundle
WORKFLOW_BUNDLE_ID = os.environ.get(
    "alfred_workflow_bundleid", "com.calebevans.jiraforalfred"
)

# The base URL for the Jira account
ACCOUNT_BASE_URL = re.sub(r"/$", "", os.environ.get("jira_base_url", ""))
# The base URL for a Jira issue
ISSUE_BASE_URL = f"{ACCOUNT_BASE_URL}/browse"
# The base URL for the Jira Cloud Platform API
API_BASE_URL = f"{ACCOUNT_BASE_URL}/rest/api/3"
# The User Agent used for all HTTP requests to the Jira Cloud Platform API
REQUEST_USER_AGENT = "Jira for Alfred (Mozilla/5.0)"
# The number of seconds to wait before timing out an HTTP request to the API
REQUEST_CONNECTION_TIMEOUT = 5


# Build the object for a single result list feedback item
def get_result_list_feedback_item(result: Result) -> Result:
    item = result.copy()

    item["text"] = result.get("text", {}).copy()
    # Text copied to clipboard when cmd-c is invoked for this result
    item["text"]["copy"] = item["text"].get("copy", result["title"])
    # Text shown when invoking Large Type for this result
    item["text"]["largetype"] = item["text"].get("largetype", result["title"])

    # Use different args when different modifiers are pressed
    item["mods"] = result.get("mods", {}).copy()
    item["mods"]["ctrl"] = item["mods"].get("ctrl", {"arg": result["title"]})

    return item


# Constructs an Alfred JSON string from the given result list
def get_result_list_feedback_str(results: Sequence[Result]) -> str:
    return json.dumps(
        {"items": [get_result_list_feedback_item(result) for result in results]}
    )


# Return the value used for the Authorization header on every API request
def get_authorization_header() -> str:
    return "{auth_type} {auth_credentials}".format(
        auth_type="Basic",
        auth_credentials=base64.standard_b64encode(
            "{id}:{secret}".format(
                id=str(os.environ.get("jira_username")).strip(),
                secret=str(os.environ.get("jira_api_token")).strip(),
            ).encode("utf-8")
        ).decode("utf-8"),
    )


# Fetch data from the Jira Cloud Platform API, optionally along with the dict of
# GET parameters
def fetch_data(endpoint_path: str, params: Optional[dict] = None) -> list:
    request_url = API_BASE_URL + endpoint_path
    if params:
        request_url += "?" + urlparse.urlencode(params)

    request = urlrequest.Request(
        request_url,
        headers={
            "User-Agent": REQUEST_USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Authorization": get_authorization_header(),
        },
    )
    try:
        response = urlrequest.urlopen(request, timeout=REQUEST_CONNECTION_TIMEOUT)
        url_content = response.read()

        # Decompress response body if gzipped
        if response.info().get("Content-Encoding") == "gzip":
            str_buf = BytesIO(url_content)
            with GzipFile(fileobj=str_buf, mode="rb") as gzip_file:
                url_content = gzip_file.read()

    except urlrequest.HTTPError as error:
        url_content = json.dumps({"issues": []}).encode("utf-8")
        raise Exception(json.loads(error.read())["errorMessages"][0])

    return json.loads(url_content.decode("utf-8"))["issues"]
