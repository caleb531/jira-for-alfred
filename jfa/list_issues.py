#!/usr/bin/env python3
# coding=utf-8

import sys

import jfa.core as core

issue_type_defs = [
    {"type": "bug", "keyword": "10303", "icon_path": "jfa/icons/bug.svg"},
    {"type": "subtask", "keyword": "10316", "icon_path": "jfa/icons/subtask.svg"},
    {"type": "task", "keyword": "10318", "icon_path": "jfa/icons/task.svg"},
    {"type": "scenario", "keyword": "10320", "icon_path": "jfa/icons/scenario.svg"},
    {"type": "test", "keyword": "10624", "icon_path": "jfa/icons/test.png"},
    {"type": "epic", "keyword": "epic", "icon_path": "jfa/icons/epic.svg"},
    {"type": "story", "keyword": "story", "icon_path": "jfa/icons/story.svg"},
]


# Retrieve an object representing the type of this particular issue
def get_issue_type_def(issue):
    for issue_type_def in issue_type_defs:
        if issue_type_def["keyword"] in issue["img"]:
            return issue_type_def
    return {"type": "unknown", "keyword": None, "icon_path": "icon.png"}


# Convert the given dictionary representation of a Jira issue to a Alfred
# feedback result dictionary
def get_result_from_issue(issue):
    issue_type_def = get_issue_type_def(issue)
    return {
        "title": issue["summaryText"],
        "subtitle": f"{issue['key']} (view in Jira)",
        "arg": issue["id"],
        "icon": {"path": issue_type_def["icon_path"]},
        "variables": {
            "issue_id": issue["id"],
            "issue_key": issue["key"],
            "issue_type": issue_type_def["type"],
            "issue_summary": issue["summaryText"],
            "issue_url": "{base_url}/browse/{issue_id}".format(
                base_url=core.ACCOUNT_BASE_URL, issue_id=issue["key"]
            ),
        },
    }


# Retrieves search resylts matching the given query
def get_result_list(query_str):
    query_str = query_str.lower()

    issues = core.fetch_data(
        "/issue/picker", params={"query": query_str, "showSubTasks": "true"}
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
