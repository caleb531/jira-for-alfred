#!/usr/bin/env python3
# coding=utf-8

import re
import sys

import jfa.core as core

# The issue types supported by this workflow
SUPPORTED_ISSUE_TYPES = {
    "bug",
    "sub-task",
    "task",
    "scenario",
    "test",
    "epic",
    "story",
}


# Retrieve the path to the icon for the given issue type; if an issue type is
# unsupported by this workflow, then the default workflow icon will be used
def get_issue_type_icon(issue_type):
    if issue_type in SUPPORTED_ISSUE_TYPES:
        return f"jfa/icons/{issue_type}.svg"
    else:
        return "icon.png"


# Convert the given dictionary representation of a Jira issue to a Alfred
# feedback result dictionary
def get_result_from_issue(issue):
    issue_type = issue["fields"]["issuetype"]["name"].lower()
    return {
        "title": issue["fields"]["summary"],
        "subtitle": f"{issue['key']} (view in Jira)",
        "arg": issue["id"],
        "icon": {"path": get_issue_type_icon(issue_type)},
        "variables": {
            "issue_id": issue["id"],
            "issue_key": issue["key"],
            "issue_type": issue_type,
            "issue_summary": issue["fields"]["summary"],
            "issue_url": "{base_url}/browse/{issue_id}".format(
                base_url=core.ACCOUNT_BASE_URL, issue_id=issue["key"]
            ),
        },
    }


# Return a boolean indicating whether or not the given query string is formatted
# like an issue key
def is_issue_key(query_str):
    return re.search(r"^[A-Z]+-[0-9]+$", query_str.upper().strip())


# Sanitize query string by removing quotes
def sanitize_query_str(query_str):
    return re.sub(r'["\']', "", query_str).strip()


# Construct the JQL expression used to search for issues matching the given
# query string
def get_search_jql(query_str):
    if is_issue_key(query_str):
        return f'issuekey = "{sanitize_query_str(query_str)}"'
    else:
        return f'summary ~ "{sanitize_query_str(query_str)}" ORDER BY updated DESC'


# Retrieves search resylts matching the given query
def get_result_list(query_str):
    query_str = query_str.lower()

    issues = core.fetch_data(
        "/search",
        params={
            "fields": "summary,issuetype",
            "jql": get_search_jql(query_str),
            "maxResults": 9,
        },
    )
    results = [get_result_from_issue(issue) for issue in issues]

    return results


def main(query_str):
    results = get_result_list(query_str)

    if not results:
        results.append(
            {
                "title": "No Results",
                "subtitle": "No issues matching '{}'".format(query_str),
                "valid": False,
            }
        )

    print(core.get_result_list_feedback_str(results))


if __name__ == "__main__":
    main(sys.argv[1])
