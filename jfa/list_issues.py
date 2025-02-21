#!/usr/bin/env python3
# coding=utf-8

import os
import re
import sys

import jfa.core as core
from jfa.types import Issue, Result

# The maximum number of results to list
MAX_RESULT_COUNT = int(os.environ.get("jira_max_result_count", "9"))

# A map of the issue types supported by this workflow
issue_type_icon_map = {
    "bug": "jfa/icons/10303.svg",
    "sub-task": "jfa/icons/10316.svg",
    "task": "jfa/icons/10318.svg",
    "epic": "jfa/icons/10307.svg",
    "story": "jfa/icons/10315.svg",
}


# Retrieve the path to the icon for the given issue type; if an issue type is
# unsupported by this workflow, then the default workflow icon will be used
def get_issue_type_icon(issue: Issue) -> str:
    avatar_id = issue["fields"].get("issuetype", {}).get("avatarId")
    icon_path = f"jfa/icons/{avatar_id}.svg"
    if avatar_id and os.path.exists(icon_path):
        return icon_path
    issue_type = issue["fields"]["issuetype"]["name"].lower()
    if issue_type in issue_type_icon_map:
        return issue_type_icon_map[issue_type]
    return "icon.png"


# Construct the URL for the issue with the given key
def get_issue_url(issue_key: str) -> str:
    return f"{core.ISSUE_BASE_URL}/{issue_key}"


# Convert the given dictionary representation of a Jira issue to a Alfred
# feedback result dictionary
def get_result_from_issue(issue: Issue) -> Result:
    issue_type = issue["fields"]["issuetype"]["name"].lower()
    return {
        "title": issue["fields"]["summary"],
        "subtitle": f"{issue['key']} (view in Jira)",
        "arg": issue["id"],
        "icon": {"path": get_issue_type_icon(issue)},
        "variables": {
            "issue_id": issue["id"],
            "issue_key": issue["key"],
            "issue_type": issue_type,
            "issue_summary": issue["fields"]["summary"],
            "issue_url": get_issue_url(issue["key"]),
        },
    }


# Return a boolean indicating whether or not the given query string is a Jira
# issue URL
def is_issue_url(query_str: str) -> bool:
    return query_str.startswith(core.ISSUE_BASE_URL)


# Return a boolean indicating whether or not the given query string is formatted
# like an issue key
def is_issue_key(query_str: str) -> bool:
    return bool(re.search(r"^[A-Z]+-[0-9]+$", query_str.upper().strip()))


# Sanitize a value for use in a JQL string
def sanitize_jql_value(jql_value: str) -> str:
    return re.sub(r'["\\]', "", jql_value).strip()


# Like the str.format() method, but sanitizes variable values into a given JQL
# string
def interpolate_variables_into_jql(jql_str: str, **variables: str) -> str:
    return jql_str.format(
        **{name: sanitize_jql_value(value) for name, value in variables.items()}
    )


# Construct an additional filter (to tack onto the start of every JQL query)
# which restricts the result set to the user-specified projects
def get_project_filter() -> str:
    project_list_str = os.environ.get("jira_restrict_to_projects", "")
    if project_list_str:
        project_keys = re.split(r",\s*", project_list_str)
        project_key_str = ", ".join(
            f"{sanitize_jql_value(key)}" for key in project_keys
        )
        return f"project IN ({project_key_str}) AND "
    else:
        return ""


# Construct the JQL expression used to search for issues matching the given
# query string
def get_search_jql(query_str: str) -> str:
    if not query_str:
        return (
            # Per the Jira Operator documentation for `WAS`, the operator will
            # match issues "that currently have or previously had the specified
            # value for the specified field" (source:
            # <https://support.atlassian.com/jira-software-cloud/docs/jql-operators/#WAS>)
            get_project_filter()
            + "assignee WAS currentuser() ORDER BY lastViewed DESC"
        )
    elif is_issue_key(query_str):
        return interpolate_variables_into_jql(
            'issuekey = "{query_str}"', query_str=query_str
        )
    else:
        return get_project_filter() + interpolate_variables_into_jql(
            'summary ~ "{query_str}*" ORDER BY lastViewed DESC',
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
    # Normalize query string by stripping leading/trailing whitespace
    query_str = query_str.strip()

    # If query string appears to be a URL to a Jira issue, convert it to an
    # issue key, then search using that issue key
    if is_issue_url(query_str):
        query_str = query_str.replace(f"{core.ISSUE_BASE_URL}/", "")

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
    main(sys.argv[1] if len(sys.argv) >= 2 else "")
