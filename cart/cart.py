from .models import CartItem
from catalog.models import Product
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.conf import settings
from django.db.models import Max
from ecomstore.settings import SESSION_AGE_DAYS
from datetime import datetime, timedelta
import decimal
import random
import logging


CART_ID_SESSION_KEY = ''


#get current user's cart id, sets new one if blank
def _cart_id(request):
	if request.session.get('CART_ID_SESSION_KEY', '') == '':
		request.session['CART_ID_SESSION_KEY'] = _generate_cart_id()
	return request.session['CART_ID_SESSION_KEY']


def _generate_cart_id():
	cart_id = ""
	characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890!@#$%^&*()'
	cart_id_length = 50
	for y in range(cart_id_length):
		cart_id += characters[ random.randint(0, len(characters)-1) ]
	return cart_id 


#return all items from the current user's cart
def get_cart_items(request):
	return CartItem.objects.filter(cart_id=_cart_id(request) )
	 


#add an item to the cart
def add_to_cart(request):
	postdata = request.POST.copy()
	product_slug = postdata.get('product_slug', "")
	quantity = postdata.get('quantity', 1)
	p = get_object_or_404(Product, slug=product_slug)
	cart_products = get_cart_items(request)
	product_in_cart = False
	 
	#check if items is already in cart
	for item in cart_products:
		if item.product.id == p.id:
			item.augment_quantity(quantity) 
			product_in_cart = True
	if not product_in_cart:
		ci = CartItem()
		ci.product = p
		ci.quantity = quantity
		ci.cart_id = _cart_id(request)
		ci.save()
	 


#returns the total number of items in the user's cart
def cart_distinct_item_count(request):
	return get_cart_items(request).count() 



def get_single_item(request, item_id):
	return get_object_or_404(CartItem, id=item_id, cart_id=_cart_id(request) )



#update quantity for single item
def update_cart(request):
	postdata = request.POST.copy() 
	item_id = postdata['item_id']
	quantity = postdata['quantity']
	cart_item = get_single_item(request, item_id)
	if cart_item:
		if int(quantity) > 0:
			cart_item.quantity = int(quantity)
			cart_item.save() 
		else:
			remove_from_cart(request) 


#remove a single item from cart
def remove_from_cart(request):
	postdata = request.POST.copy()
	item_id = postdata['item_id']
	cart_item = get_single_item(request, item_id)
	if cart_item:
		cart_item.delete()
		 



#gets the total cost for the current cart
def cart_subtotal(request):
	cart_total = decimal.Decimal('0.00')
	cart_products = get_cart_items(request)
	for item in cart_products:
		cart_total += item.product.price * item.quantity 
	return cart_total



def is_empty(request):
	return cart_distinct_item_count(request) == 0



def empty_cart(request):
	user_cart = get_cart_items(request)
	user_cart.delete()

	


#remove old shopping cart items from db.
def remove_old_cart_items():
	print 'remove old carts'
	#calculate date of SESSION_AGE_DAYS days ago
	remove_before = datetime.now() + timedelta(days=-settings.SESSION_AGE_DAYS)
	cart_ids = []

	old_items = CartItem.objects.values('cart_id').annotate(last_change=Max('date_added')).filter(last_change__lt=remove_before).order_by()

	#create a list of cart IDs that haven't been modified
	for item in old_items:
		cart_ids.append(item['cart-id'])
		to_remove = CartItems.objects.filter(cart_id__in=cart_ids)
		to_remove.delete() 
	print str(len(cart_ids)) + 'carts were removed' 

























