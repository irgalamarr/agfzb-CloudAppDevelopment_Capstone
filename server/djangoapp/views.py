from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .models import DealerReview, CarModel
from .restapis import get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Constants for URLs
DEALERSHIP_URL = "https://irgalamarr-3000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/dealerships/get"
DEALER_DETAILS_URL = "https://irgalamarr-5000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/get_reviews"
ADD_REVIEW_URL = "https://irgalamarr-5000.theiadockernext-1-labs-prod-theiak8s-4-tor01.proxy.cognitiveclass.ai/api/post_review"

# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/user_login.html', context)
    else:
        return render(request, 'djangoapp/user_login.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(DEALERSHIP_URL)
        context['dealership_list'] = dealerships
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        context = {}
        dealerships = get_dealers_from_cf(DEALERSHIP_URL, id=dealer_id)
        context['dealership'] = dealerships[0]
        dealership_reviews = get_dealer_reviews_from_cf(DEALER_DETAILS_URL, id=dealer_id)
        context['review_list'] = dealership_reviews
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    if request.method == "GET":
        context = {}
        dealerships = get_dealers_from_cf(DEALERSHIP_URL, id=dealer_id)
        car_models = CarModel.objects.filter(dealer_id=dealer_id)
        context['cars'] = car_models
        context['dealership'] = dealerships[0]
        context['dealer_id'] = dealer_id
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == "POST":
        if request.user.is_authenticated:
            review = dict()
            review["id"] = 1
            review["dealership"] = dealer_id
            review["name"] = request.POST.get('content')
            review["review"] = request.POST.get('content')
            review["purchase"] = request.POST.get('purchasecheck') == "on"
            review["purchase_date"] = request.POST.get('purchasedate')
            car_models = CarModel.objects.filter(id=request.POST.get('car'))
            car_model = car_models[0]
            review["car_make"] = car_model.make.name
            review["car_model"] = car_model.name
            review["car_year"] = str(car_model.year)[0:4]
            response = post_request(ADD_REVIEW_URL, review, dealerId=dealer_id)
        return redirect("djangoapp:dealer_details", dealer_id=dealer_id)
