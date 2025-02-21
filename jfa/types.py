#!/usr/bin/env python3

from typing import Optional, TypedDict


class IssueType(TypedDict):
    name: str
    iconUrl: str
    avatarId: Optional[str]


class IssueFields(TypedDict):
    summary: str
    issuetype: IssueType


class Issue(TypedDict):
    id: str
    key: str
    fields: IssueFields


class ResultIcon(TypedDict):
    path: str


class ResultVariables(TypedDict):
    issue_id: str
    issue_key: str
    issue_type: str
    issue_summary: str
    issue_url: str


class ResultText(TypedDict, total=False):
    copy: str
    largetype: str


class ResultMod(TypedDict, total=False):
    title: str
    subtitle: str
    arg: str
    valid: bool


class ResultMods(TypedDict, total=False):
    ctrl: ResultMod


class Result(TypedDict, total=False):
    title: str
    subtitle: str
    arg: str
    valid: bool
    icon: ResultIcon
    variables: ResultVariables
    text: ResultText
    mods: ResultMods
