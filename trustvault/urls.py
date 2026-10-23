
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    # TrustVault application
    path("", include("vault.urls")),

    # Django administration
    path("admin/", admin.site.urls),

    # Sign in and sign out
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),

    # Forgot password: request a reset link
    path(
        "accounts/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),

    # Change password: signed-in users
    path(
        "accounts/password-change/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change_form.html",
        ),
        name="password_change",
    ),
    path(
        "accounts/password-change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html",
        ),
        name="password_change_done",
    ),
]
