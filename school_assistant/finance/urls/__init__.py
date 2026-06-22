from django.urls import path, include

urlpatterns = [
    path("", include("finance.urls.admin")),
    # finance.urls.others -- /api/finance/my-fees and /api/finance/statement/{id}, built by Dev B
]