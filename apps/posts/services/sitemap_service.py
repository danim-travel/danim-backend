from apps.posts.models import Post


class SitemapService:
    def get_sitemap_posts(self):
        return Post.objects.order_by("id").values("id", "updated_at")
