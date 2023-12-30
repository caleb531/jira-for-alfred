#!/usr/bin/env python3
# coding=utf-8

import re
import sys

import jfa.core as core
from jfa.types import Issue, Result

# The maximum number of results to list
MAX_RESULT_COUNT = 9

# A map of the issue types supported by this workflow
issue_type_icon_map = {
    "bug": "jfa/icons/bug.svg",
    "sub-task": "jfa/icons/subtask.svg",
    "task": "jfa/icons/task.svg",
    "scenario": "jfa/icons/scenario.svg",
    "test": "jfa/icons/test.png",
    "epic": "jfa/icons/epic.svg",
    "story": "jfa/icons/story.svg",
}


# Retrieve the path to the icon for the given issue type; if an issue type is
# unsupported by this workflow, then the default workflow icon will be used
def get_issue_type_icon(issue_type: str) -> str:
    if issue_type in issue_type_icon_map:
        return issue_type_icon_map[issue_type]
    else:
        return "icon.png"


# Convert the given dictionary representation of a Jira issue to a Alfred
# feedback result dictionary
def get_result_from_issue(issue: Issue) -> Result:
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
def is_issue_key(query_str: str) -> bool:
    return bool(re.search(r"^[A-Z]+-[0-9]+$", query_str.upper().strip()))


# Sanitize a value for use in a JQL string
def sanitize_jql_value(jql_value: str) -> str:
    return re.sub(r'["]', "", jql_value).strip()


# Like the str.format() method, but sanitizes variable values into a given JQL
# string
def interpolate_variables_into_jql(jql_str: str, **variables: str) -> str:
    return jql_str.format(
        **{name: sanitize_jql_value(value) for name, value in variables.items()}
    )


# Construct the JQL expression used to search for issues matching the given
# query string
def get_search_jql(query_str: str) -> str:
    if is_issue_key(query_str):
        return interpolate_variables_into_jql(
            'issuekey = "{query_str}"', query_str=query_str
        )
    else:
        return interpolate_variables_into_jql(
            'summary ~ "{query_str}*" AND lastViewed IS NOT NULL ORDER BY lastViewed DESC',  # noqa: E501
            query_str=query_str,
        )


# Retrieves search resylts matching the given query
def get_result_list(query_str: str) -> list[Result]:
    query_str = query_str.lower()

    issues = core.fetch_data(
        "/search",
        params={
            "fields": "summary,issuetype",
            "jql": get_search_jql(query_str),
            "maxResults": MAX_RESULT_COUNT,
        },
    )
    results = [get_result_from_issue(issue) for issue in issues]

    return results


def main(query_str: str) -> None:
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
