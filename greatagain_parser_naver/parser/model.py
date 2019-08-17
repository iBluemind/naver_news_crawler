# -*- coding: utf-8 -*-

from typing import Optional


class Article:
    uid: str
    title: str
    content: str
    comments_count: int
    initialized_at: str
    url: str

    def __init__(self, uid, title, content,
                 comments_count, initialized_at,
                 url):
        self.uid = uid
        self.title = title
        self.content = content
        self.comments_count = comments_count
        self.initialized_at = initialized_at
        self.url = url


class Comment:
    uid: str
    user_id: str
    username: str
    nickname: str
    content: str
    reply_count: Optional[int]
    like_count: int
    dislike_count: int
    registered_at: str
    modified_at: str
    children: list

    def __init__(self, uid, user_id, username,
                 nickname, content, reply_count,
                 like_count, dislike_count,
                 registered_at, modified_at):
        self.uid = uid
        self.user_id = user_id
        self.username = username
        self.nickname = nickname
        self.content = content
        self.reply_count = reply_count
        self.like_count = like_count
        self.dislike_count = dislike_count
        self.registered_at = registered_at
        self.modified_at = modified_at


class ChildComment(Comment):
    parent_uid: str

    def __init__(self, uid, parent_uid, user_id,
                 username, nickname, content,
                 like_count, dislike_count, registered_at,
                 modified_at):
        super(ChildComment, self).__init__(
            uid=uid,
            user_id=user_id,
            username=username,
            nickname=nickname,
            content=content,
            like_count=like_count,
            dislike_count=dislike_count,
            registered_at=registered_at,
            modified_at=modified_at,
            reply_count=None
        )

        self.parent_uid = parent_uid
