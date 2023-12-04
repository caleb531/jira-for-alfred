#!/usr/bin/env python3
# coding=utf-8

import sys

import jfa.core as core


# Convert the given dictionary representation of a Jira issue to a Alfred
# feedback result dictionary
def get_result_from_issue(issue):
    return {
        "title": issue["summaryText"],
        "subtitle": f"{issue['key']} (view in Jira)",
        "arg": issue["id"],
        "variables": {
            "issue_id": issue["id"],
            "issue_key": issue["key"],
            "issue_summary": issue["summaryText"],
            "issue_url": "{base_url}/browse/{issue_id}".format(
                base_url=core.ACCOUNT_BASE_URL, issue_id=issue["key"]
            ),
        },
    }


# Retrieves search resylts matching the given query
def get_result_list(query_str):
    query_str = query_str.lower()

    issues = core.fetch_data("/issue/picker", params={"query": query_str})
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
