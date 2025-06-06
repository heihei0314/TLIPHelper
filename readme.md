# 1. Create a new Django project
django-admin startproject TLIPHelper
cd TLIPHelper

# 2. Create an app to manage the guide
python manage.py startapp guide

# 3. Open TLIPHelper/settings.py and add 'guide' to your INSTALLED_APPS
INSTALLED_APPS = [
    # ... other apps
    'django.contrib.staticfiles',
    'guide', # Add this line
]

# 4. Run Migrations
python manage.py makemigrations guide
python manage.py migrate

python manage.py createsuperuser
# Follow the prompts to create your admin account

# 5. Run the development server
python manage.py runserver

# 6. Open your browser and navigate to http://127.0.0.1:8000/


# Main Directory Structure
TLIPHelper/
├── readme.md
├── manage.py
├── guide/ ( This is the Django App we created. It contains the specific functionality for the proposal guide feature.)
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── urls.py
│   ├── models.py
│   ├── tests.py
│   ├── views.py
│   ├── static/
│   │   ├──  css/
│   │   └──  js/
│   └── templates/
│       └──  proposal_guide.html/
├── proposal_builder/ (This is the Project Configuration Directory. It contains project-wide settings.)
│   ├── __init__.py
│   ├── settings.py
│   ├── SECRET_KEY
│   ├── DEBUG
│   ├── INSTALLED_APPS
│   ├── STATIC_URL
│   ├── asgi.py
│   └── wsgi.py