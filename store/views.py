# -*- coding: utf-8 -*-
# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from datetime import datetime

from .models import Wallet
from .mongodb_utils import MongoWallet, MongoTransaction, mongo_connection
def register_view(request):
    # Clear any existing messages before processing the registration page
    storage = messages.get_messages(request)
    for message in storage:
        pass  # This consumes and clears all existing messages

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Save user to Django database
            user = form.save()

            # Store user data in MongoDB
            try:
                users_collection = mongo_connection.get_collection('users')
                if users_collection:
                    user_data = {
                        'user_id': user.id,
                        'username': user.username,
                        'email': getattr(user, 'email', ''),
                        'date_joined': datetime.now(),
                        'is_active': True
                    }
                    users_collection.insert_one(user_data)

                # Create wallet in MongoDB
                MongoWallet.get_or_create_wallet(user.id, user.username)

                messages.success(request, 'Registration successful. Please log in.')
            except Exception as e:
                messages.warning(request, 'Registration successful, but there was an issue with wallet setup.')

            return redirect('login')  # ✅ Redirect to login instead of index
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def index(request):
    products = [
        {'id': 1, 'name': 'Premium T-Shirt', 'price': 15, 'image': 'images/i8.avif'},
        {'id': 2, 'name': 'Running Shoes', 'price': 40, 'image': 'images/shoes.jpg'},
        {'id': 3, 'name': 'Smart Watch', 'price': 120, 'image': 'images/watch.jpg'},
        {'id': 4, 'name': 'Wireless Earbuds', 'price': 80, 'image': 'images/i1.avif'},
    ]
    return render(request, 'store/index.html', {'products': products})
def add_to_cart(request, product_id):
    cart = request.session.get('cart', [])
    product_map = {
        1: {'id': 1, 'name': 'Premium T-Shirt', 'price': 15, 'image': 'images/i8.avif'},
        2: {'id': 2, 'name': 'Running Shoes', 'price': 40, 'image': 'images/shoes.avif'},
        3: {'id': 3, 'name': 'Smart Watch', 'price': 120, 'image': 'images/watch.avif'},
        4: {'id': 4, 'name': 'Wireless Earbuds', 'price': 80, 'image': 'images/i1.avif'},
    }
    if product_id in product_map:
        product = product_map[product_id]
        # Check if product already exists in cart
        existing_item = None
        for item in cart:
            if item.get('id') == product_id:
                existing_item = item
                break

        if existing_item:
            # If item exists, increase quantity (add quantity field if not exists)
            existing_item['quantity'] = existing_item.get('quantity', 1) + 1
            messages.success(request, f'{product["name"]} quantity updated in cart!')
        else:
            # Add new item with quantity
            product['quantity'] = 1
            cart.append(product)
            messages.success(request, f'{product["name"]} added to cart!')

        request.session['cart'] = cart
        request.session.modified = True  # Ensure session is saved

        # Store cart data in MongoDB if user is logged in
        if request.user.is_authenticated:
            try:
                carts_collection = mongo_connection.get_collection('carts')
                if carts_collection:
                    # Update or create cart in MongoDB
                    cart_data = {
                        'user_id': request.user.id,
                        'username': request.user.username,
                        'cart_items': cart,
                        'total_items': len(cart),
                        'total_amount': sum(item['price'] * item.get('quantity', 1) for item in cart),
                        'updated_at': datetime.now()
                    }

                    # Update existing cart or insert new one
                    carts_collection.update_one(
                        {'user_id': request.user.id},
                        {'$set': cart_data},
                        upsert=True
                    )
            except Exception as e:
                # Don't show error to user, just log it
                pass

    else:
        messages.error(request, 'Product not found!')
    return redirect('index')
def cart_view(request):
    cart = request.session.get('cart', [])
    total = sum(item['price'] * item.get('quantity', 1) for item in cart)
    print(f"=== CART DEBUG ===")
    print(f"User: {request.user}")
    print(f"Session key: {request.session.session_key}")
    print(f"Cart items count: {len(cart)}")
    print(f"Raw cart data: {cart}")
    print(f"Calculated total: {total}")
    print("Individual items:")
    for i, item in enumerate(cart):
        item_total = item['price'] * item.get('quantity', 1)
        print(f"  {i+1}. {item['name']} - ${item['price']} × {item.get('quantity', 1)} = ${item_total}")
    print(f"=== END DEBUG ===")
    return render(request, 'store/add.html', {'cart': cart, 'total': total})
def clear_cart(request):
    request.session['cart'] = []
    messages.success(request, 'Cart cleared successfully!')
    return redirect('cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', [])
    # Find and remove the item with the matching product_id
    cart = [item for item in cart if item.get('id') != product_id]
    request.session['cart'] = cart
    request.session.modified = True
    messages.success(request, 'Item removed from cart!')
    return redirect('cart')

def update_cart_quantity(request, product_id):
    if request.method == 'POST':
        cart = request.session.get('cart', [])
        change = int(request.POST.get('change', 0))

        # Find the item in cart
        for item in cart:
            if item.get('id') == product_id:
                current_quantity = item.get('quantity', 1)
                new_quantity = current_quantity + change

                if new_quantity <= 0:
                    # Remove item if quantity becomes 0 or negative
                    cart = [i for i in cart if i.get('id') != product_id]
                    messages.success(request, f'{item["name"]} removed from cart!')
                else:
                    # Update quantity
                    item['quantity'] = new_quantity
                    messages.success(request, f'{item["name"]} quantity updated!')
                break

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart')




@login_required
def pay(request):
    # Get Django wallet
    wallet, created = Wallet.objects.get_or_create(user=request.user)

    # Get MongoDB wallet balance (fallback to Django wallet if MongoDB fails)
    try:
        mongo_balance = MongoWallet.get_balance(request.user.id)
        # Use MongoDB balance if available, otherwise use Django wallet
        wallet_balance = mongo_balance if mongo_balance is not None else wallet.balance
    except Exception as e:
        wallet_balance = wallet.balance

    cart = request.session.get('cart', [])
    total = sum(item['price'] * item.get('quantity', 1) for item in cart)

    # Get transaction history from MongoDB
    try:
        transactions = MongoTransaction.get_user_transactions(request.user.id, limit=10)
    except:
        transactions = []

    return render(request, 'store/pay.html', {
        'wallet_balance': wallet_balance,
        'cart': cart,
        'total': total,
        'transactions': transactions,
    })





@login_required
def recharge_wallet(request):
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        try:
            amount = Decimal(amount_str)
            if amount > 0:
                # Update Django wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.balance += amount
                wallet.save()

                # Update MongoDB wallet
                try:
                    # Get current MongoDB balance
                    mongo_balance = MongoWallet.get_balance(request.user.id)
                    new_mongo_balance = mongo_balance + amount

                    # Update MongoDB wallet
                    MongoWallet.update_balance(request.user.id, new_mongo_balance)

                    # Create transaction record in MongoDB
                    MongoTransaction.create_transaction(
                        user_id=request.user.id,
                        username=request.user.username,
                        transaction_type='credit',
                        amount=amount,
                        description=f'Wallet recharge of ₹{amount}',
                        balance_after=new_mongo_balance
                    )

                except Exception as mongo_error:
                    # MongoDB operation failed, but Django wallet was updated
                    pass

                messages.success(request, f"₹{amount} added to your wallet successfully.")
            else:
                messages.error(request, "Invalid amount.")
        except Exception as e:
            messages.error(request, f"Recharge failed: {str(e)}")

    return redirect('pay')  # Make sure this matches your urls.py

@login_required
def process_payment(request):
    """Process payment and update MongoDB with transaction details"""
    if request.method == 'POST':
        try:
            payment_method = request.POST.get('method', 'wallet')
            cart = request.session.get('cart', [])

            print(f"=== PAYMENT DEBUG ===")
            print(f"User: {request.user.username}")
            print(f"Payment method: {payment_method}")
            print(f"Cart: {cart}")
            print(f"=== END PAYMENT DEBUG ===")

            if not cart:
                messages.error(request, 'Your cart is empty!')
                return redirect('cart')

            # Calculate total
            total_amount = sum(item['price'] * item.get('quantity', 1) for item in cart)
            total_amount = Decimal(str(total_amount))

            if payment_method == 'wallet':
                # Get current wallet balance from MongoDB
                try:
                    current_balance = MongoWallet.get_balance(request.user.id)

                    # If MongoDB balance is 0, check Django wallet and sync
                    if current_balance == 0:
                        # Check Django wallet
                        django_wallet, created = Wallet.objects.get_or_create(user=request.user)

                        # If Django wallet has balance, sync to MongoDB
                        if django_wallet.balance > 0:
                            MongoWallet.update_balance(request.user.id, django_wallet.balance)
                            current_balance = django_wallet.balance
                        else:
                            # Create wallet record if needed
                            wallet_record = MongoWallet.get_or_create_wallet(request.user.id, request.user.username)
                            if wallet_record:
                                current_balance = Decimal(str(wallet_record.get('balance', 0)))

                except Exception as e:
                    # Fallback to Django wallet
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    current_balance = wallet.balance

                # Check if sufficient balance
                if current_balance < total_amount:
                    messages.error(request, f'Insufficient wallet balance! You have ₹{current_balance}, but need ₹{total_amount}.')
                    return redirect('pay')

                # Process wallet payment
                new_balance = current_balance - total_amount

                # Update Django wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.balance = new_balance
                wallet.save()

                # Update MongoDB wallet
                try:
                    MongoWallet.update_balance(request.user.id, new_balance)

                    # Create payment transaction in MongoDB
                    MongoTransaction.create_transaction(
                        user_id=request.user.id,
                        username=request.user.username,
                        transaction_type='debit',
                        amount=total_amount,
                        description=f'Purchase payment - {len(cart)} items',
                        balance_after=new_balance
                    )

                    # Store purchase details in MongoDB
                    purchases_collection = mongo_connection.get_collection('purchases')
                    if purchases_collection:
                        purchase_data = {
                            'user_id': request.user.id,
                            'username': request.user.username,
                            'items': cart,
                            'total_amount': float(total_amount),
                            'payment_method': payment_method,
                            'payment_status': 'completed',
                            'purchase_date': datetime.now(),
                            'balance_before': float(current_balance),
                            'balance_after': float(new_balance)
                        }
                        purchases_collection.insert_one(purchase_data)

                except Exception as mongo_error:
                    # MongoDB failed but Django wallet was updated
                    pass

                # Clear cart after successful payment
                request.session['cart'] = []
                request.session.modified = True

                # Clear cart in MongoDB if user has one
                try:
                    carts_collection = mongo_connection.get_collection('carts')
                    if carts_collection:
                        carts_collection.delete_one({'user_id': request.user.id})
                except:
                    pass

                messages.success(request, f'🎉 PAYMENT SUCCESSFUL! ₹{total_amount} deducted from wallet. New balance: ₹{new_balance}')
                return redirect('pay')

            else:
                # For other payment methods (UPI, Card, etc.)
                # In a real app, you would integrate with payment gateways
                messages.info(request, f'Payment method {payment_method} is not yet implemented. Please use wallet payment.')
                return redirect('pay')

        except Exception as e:
            messages.error(request, f'Payment processing failed: {str(e)}')
            return redirect('pay')

    return redirect('pay')

@login_required
def mongodb_dashboard(request):
    """MongoDB Dashboard view to display MongoDB data"""
    try:
        # Get MongoDB collections data
        users_collection = mongo_connection.get_collection('users')
        wallets_collection = mongo_connection.get_collection('wallets')
        transactions_collection = mongo_connection.get_collection('transactions')
        carts_collection = mongo_connection.get_collection('carts')
        purchases_collection = mongo_connection.get_collection('purchases')

        # Get collection statistics
        stats = {
            'users': users_collection.count_documents({}) if users_collection else 0,
            'wallets': wallets_collection.count_documents({}) if wallets_collection else 0,
            'transactions': transactions_collection.count_documents({}) if transactions_collection else 0,
            'carts': carts_collection.count_documents({}) if carts_collection else 0,
            'purchases': purchases_collection.count_documents({}) if purchases_collection else 0,
        }

        # Get recent transactions
        recent_transactions = []
        if transactions_collection:
            transactions_cursor = transactions_collection.find().sort('timestamp', -1).limit(10)
            recent_transactions = list(transactions_cursor)

        # Get user's wallet info
        user_wallet = None
        if wallets_collection:
            user_wallet = wallets_collection.find_one({'user_id': request.user.id})

        # Get user's cart
        user_cart = None
        if carts_collection:
            user_cart = carts_collection.find_one({'user_id': request.user.id})

        context = {
            'stats': stats,
            'recent_transactions': recent_transactions,
            'user_wallet': user_wallet,
            'user_cart': user_cart,
            'mongodb_connected': True
        }

    except Exception as e:
        context = {
            'mongodb_connected': False,
            'error': str(e)
        }

    return render(request, 'store/mongodb_dashboard.html', context)


