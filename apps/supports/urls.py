from django.urls import URLPattern, path

from apps.supports.views import (
    FAQCategoryListView,
    FAQDetailView,
    FAQFeedbackView,
    FAQListView,
)

app_name = "supports"

urlpatterns: list[URLPattern] = [
    # /faqs/categories가 /faqs/<faq_id>보다 먼저 매치되어야 한다
    path("/faqs/categories", FAQCategoryListView.as_view(), name="faq_categories"),
    path("/faqs", FAQListView.as_view(), name="faq_list"),
    path("/faqs/<str:faq_id>", FAQDetailView.as_view(), name="faq_detail"),
    path(
        "/faqs/<str:faq_id>/feedback",
        FAQFeedbackView.as_view(),
        name="faq_feedback",
    ),
]
