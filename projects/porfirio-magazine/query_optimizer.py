"""Portfolio excerpt, adapted."""
from collections import defaultdict

from sqlalchemy.orm import joinedload, selectinload


class OptimizedQueries:
    """Read-optimized queries for common views."""

    @staticmethod
    def get_published_articles_with_relations(limit=20, offset=0):
        """Return published articles with author, category, and comments eager-loaded."""
        from src.models.article import Article

        return (
            Article.query
            .filter_by(published=True)
            .options(
                joinedload(Article.author),
                joinedload(Article.category),
                selectinload(Article.comments),
            )
            .order_by(Article.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

    @staticmethod
    def get_article_by_slug_optimized(slug):
        """Return the article plus every relation the detail view needs, in one round trip."""
        from src.models.article import Article
        from src.models.comment import Comment

        return (
            Article.query
            .filter_by(slug=slug, published=True)
            .options(
                joinedload(Article.author),
                joinedload(Article.category),
                selectinload(Article.comments).joinedload(Comment.user),
                selectinload(Article.favorites),
            )
            .first()
        )

    @staticmethod
    def get_comments_for_article_threaded(article_id):
        """Return (roots, replies_by_parent) for an article's approved comments.

        One query for the whole thread, then assembled in Python. Replies keyed by
        parent_id so the caller walks the tree without triggering a query per node.
        """
        from src.models.comment import Comment

        all_comments = (
            Comment.query
            .filter_by(article_id=article_id, status='approved')
            .options(joinedload(Comment.user))
            .order_by(Comment.created_at.asc())
            .all()
        )

        replies_by_parent = defaultdict(list)
        roots = []
        for comment in all_comments:
            if comment.parent_id is None:
                roots.append(comment)
            else:
                replies_by_parent[comment.parent_id].append(comment)

        return roots, replies_by_parent


# N+1 vs. eager-loaded
#
# bad: `article.author` in the loop fires one query per row
#     articles = Article.query.filter_by(published=True).all()
#     return [{'author': a.author.username, 'category': a.category.name}
#             for a in articles]
#
# good: joinedload/selectinload pulls the relations up front
#     articles = OptimizedQueries.get_published_articles_with_relations(
#         limit=per_page, offset=offset,
#     )
#     return [{'author': a.author.username, 'category': a.category.name}
#             for a in articles]
