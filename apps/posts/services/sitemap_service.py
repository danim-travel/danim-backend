from apps.posts.models import Post


class SitemapService:
    def get_sitemap_posts(self):
        return Post.objects.only("id", "updated_at").order_by("id")
