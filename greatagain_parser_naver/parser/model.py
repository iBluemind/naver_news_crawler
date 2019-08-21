# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional


class Article:
    uid: str
    title: str
    content: str
    comments_count: int
    initialized_at: str
    finalized_at: str
    url: str
    press: str
    author: Optional[str]
    reactions: int
    recommends: Optional[int]

    def __init__(self, uid, title, content,
                 comments_count, initialized_at,
                 url, press, reactions, author=None, recommends=None):
        self.uid = uid
        self.title = title
        self.content = content
        self.comments_count = comments_count
        self.initialized_at = initialized_at
        self.url = url
        self.press = press
        self.author = author
        self.reactions = reactions
        self.recommends = recommends


class ArticleHistory:
    article_uid: str
    title: str
    content: str
    created_at: datetime
    comments_count: int
    reactions: int
    recommends: Optional[int]

    def __init__(self, article_uid, title, content,
                 comments_count, reactions, recommends=None):
        self.article_uid = article_uid
        self.title = title
        self.content = content
        self.comments_count = comments_count
        self.reactions = reactions
        self.recommends = recommends
        self.created_at = datetime.now()


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
    article_uid: str
    exposed: bool
    deleted: bool

    def __init__(self, uid, user_id, username,
                 nickname, content, reply_count,
                 like_count, dislike_count,
                 registered_at, modified_at,
                 exposed, deleted):
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
        self.exposed = exposed
        self.deleted = deleted


class ChildComment(Comment):
    parent_uid: str

    def __init__(self, uid, parent_uid, user_id,
                 username, nickname, content,
                 like_count, dislike_count, registered_at,
                 modified_at, exposed, deleted):
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
            reply_count=None,
            exposed=exposed,
            deleted=deleted
        )

        self.parent_uid = parent_uid

class CommentsCountHistory:
    article_uid: str
    comments_count: int
    created_at: datetime

    def __init__(self, article_uid, comments_count):
        self.article_uid = article_uid
        self.comments_count = comments_count
        self.created_at = datetime.now()
