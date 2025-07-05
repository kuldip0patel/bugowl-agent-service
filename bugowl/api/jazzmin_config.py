"""
Django Admin Theme Configuration using Jazzmin
BugOwl Agent Service - Custom Admin Theme

This file contains all Jazzmin configuration settings for the Django admin interface.
It's imported into settings.py to keep the main settings file clean.

Colors:
- Primary: #1188cc (Blue)
- Secondary: #aaaa00 (Yellow)

To customize the theme:
1. Edit the settings in this file
2. Modify the CSS in static/admin/css/custom_admin.css
3. Replace the logo in static/admin/img/logo.svg
4. Run: python manage.py collectstatic --noinput
5. Restart Django service

Documentation: https://django-jazzmin.readthedocs.io/
"""

# Jazzmin Django Admin Theme Configuration
JAZZMIN_SETTINGS = {
	# title of the window (Will default to current_admin_site.site_title if absent or None)
	'site_title': 'BugOwl Agent Admin',
	# Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
	'site_header': 'BugOwl Agent',
	# Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
	'site_brand': 'BugOwl Agent',
	# Logo to use for your site, must be present in static files, used for brand on top left
	'site_logo': 'admin/img/logo.svg',
	# Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
	'login_logo': 'admin/img/logo.svg',
	# Logo to use for login form in dark themes (defaults to login_logo)
	'login_logo_dark': 'admin/img/logo.svg',
	# CSS classes that are applied to the logo above
	'site_logo_classes': 'img-circle',
	# Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
	'site_icon': 'admin/img/logo.svg',
	# Welcome text on the login screen
	'welcome_sign': 'Welcome to BugOwl Agent Admin',
	# Copyright on the footer
	'copyright': 'BugOwl Agent Service',
	# List of model admins to search from the search bar, search bar omitted if excluded
	# If you want to use a single search field you dont need to use a list, you can use a simple string
	'search_model': ['auth.User', 'auth.Group'],
	# Field name on user model that contains avatar ImageField/URLField/Charfield or a callable that receives the user
	'user_avatar': None,
	############
	# Top Menu #
	############
	# Links to put along the top menu
	'topmenu_links': [
		# Url that gets reversed (Permissions can be added)
		{'name': 'Home', 'url': 'admin:index', 'permissions': ['auth.view_user']},
		# external url that opens in a new window (Permissions can be added)
		{'name': 'Support', 'url': 'https://github.com/farridav/django-jazzmin/issues', 'new_window': True},
		# model admin to link to (Permissions checked against model)
		{'model': 'auth.User'},
		# App with dropdown menu to all its models pages (Permissions checked against models)
		{'app': 'testcase'},
	],
	#############
	# User Menu #
	#############
	# Additional links to include in the user menu on the top right ("app" url type is not allowed)
	'usermenu_links': [
		{'name': 'Support', 'url': 'https://github.com/farridav/django-jazzmin/issues', 'new_window': True},
		{'model': 'auth.user'},
	],
	#############
	# Side Menu #
	#############
	# Whether to display the side menu
	'show_sidebar': True,
	# Whether to aut expand the menu
	'navigation_expanded': True,
	# Hide these apps when generating side menu e.g (auth)
	'hide_apps': [],
	# Hide these models when generating side menu (e.g auth.user)
	'hide_models': [],
	# List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
	'order_with_respect_to': ['auth', 'testcase', 'teststep', 'testask'],
	# Custom links to append to app groups, keyed on app name
	'custom_links': {
		'testcase': [
			{
				'name': 'Make Messages',
				'url': 'make_messages',
				'icon': 'fas fa-comments',
				'permissions': ['testcase.view_testcase'],
			}
		]
	},
	# Custom icons for side menu apps/models See https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.5.0,5.6.0,5.6.1,5.6.3,5.7.0,5.7.1,5.7.2,5.8.0,5.8.1,5.8.2,5.9.0,5.10.0,5.10.1,5.10.2,5.11.0,5.11.1,5.11.2,5.12.0,5.12.1,5.13.0,5.13.1,5.14.0,5.15.0,5.15.1,5.15.2,5.15.3,5.15.4&s=solid
	'icons': {
		'auth': 'fas fa-users-cog',
		'auth.user': 'fas fa-user',
		'auth.Group': 'fas fa-users',
		'testcase': 'fas fa-vial',
		'testcase.TestCase': 'fas fa-flask',
		'testcase.TestCaseRun': 'fas fa-play-circle',
		'teststep': 'fas fa-list-ol',
		'teststep.TestStep': 'fas fa-step-forward',
		'teststep.TestStepRun': 'fas fa-running',
		'testask': 'fas fa-tasks',
		'testask.TestTask': 'fas fa-clipboard-list',
		'testask.TestTaskRun': 'fas fa-clipboard-check',
	},
	# Icons that are used when one is not manually specified
	'default_icon_parents': 'fas fa-chevron-circle-right',
	'default_icon_children': 'fas fa-circle',
	#################
	# Related Modal #
	#################
	# Use modals instead of popups
	'related_modal_active': False,
	#############
	# UI Tweaks #
	#############
	# Relative paths to custom CSS/JS scripts (must be present in static files)
	'custom_css': 'admin/css/custom_admin.css',
	'custom_js': None,
	# Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
	'use_google_fonts_cdn': True,
	# Whether to show the UI customizer on the sidebar
	'show_ui_builder': True,
	###############
	# Change view #
	###############
	# Render out the change view as a single form, or in tabs, current options are
	# - single
	# - horizontal_tabs (default)
	# - vertical_tabs
	# - collapsible
	# - carousel
	'changeform_format': 'horizontal_tabs',
	# override change forms on a per modeladmin basis
	'changeform_format_overrides': {'auth.user': 'collapsible', 'auth.group': 'vertical_tabs'},
	# Add a language dropdown into the admin
	'language_chooser': False,
}

# Jazzmin UI Tweaks
JAZZMIN_UI_TWEAKS = {
	'navbar_small_text': False,
	'footer_small_text': False,
	'body_small_text': False,
	'brand_small_text': False,
	'brand_colour': 'navbar-info',  # Using info for the blue color
	'accent': 'accent-warning',  # Using warning for the yellow accent
	'navbar': 'navbar-dark',
	'no_navbar_border': False,
	'navbar_fixed': False,
	'layout_boxed': False,
	'footer_fixed': False,
	'sidebar_fixed': False,
	'sidebar': 'sidebar-dark-info',  # Dark sidebar with blue accent
	'sidebar_nav_small_text': False,
	'sidebar_disable_expand': False,
	'sidebar_nav_child_indent': False,
	'sidebar_nav_compact_style': False,
	'sidebar_nav_legacy_style': False,
	'sidebar_nav_flat_style': False,
	'theme': 'default',
	'dark_mode_theme': None,
	'button_classes': {
		'primary': 'btn-primary',
		'secondary': 'btn-warning',  # Using warning (yellow) for secondary
		'info': 'btn-info',
		'warning': 'btn-warning',
		'danger': 'btn-danger',
		'success': 'btn-warning',  # Using warning (yellow) for success
	},
	'actions_sticky_top': False,
}
