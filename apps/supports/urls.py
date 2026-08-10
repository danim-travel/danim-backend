from django.urls import URLPattern, path

from apps.supports.views import (
    FAQCategoryListView,
    FAQDetailView,
    FAQFeedbackView,
    FAQListView,
    InquiryDetailView,
    InquiryListCreateView,
    InquiryPresignedUrlView,
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
    # 위와 같은 이유로 /inquiries/presigned-url이 /inquiries/<inquiry_id>보다 먼저다
    path(
        "/inquiries/presigned-url",
        InquiryPresignedUrlView.as_view(),
        name="inquiry_presigned_url",
    ),
    path("/inquiries", InquiryListCreateView.as_view(), name="inquiry_list_create"),
    path(
        "/inquiries/<str:inquiry_id>",
        InquiryDetailView.as_view(),
        name="inquiry_detail",
    ),
]
