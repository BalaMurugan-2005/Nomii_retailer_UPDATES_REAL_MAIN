import os
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from flask import Flask, render_template, request, redirect, url_for, session, flash
import re
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Excel file paths
EXCEL_FILES = {
    'retailer_users': 'data/retailer_users.xlsx',
    'products': 'data/Products.xlsx',
    'retailer_orders': 'data/retailer_orders.xlsx',
    'orders': 'data/Orders.xlsx',
    'delivery_status': 'data/deliverystatus.xlsx',
    'money_spent': 'data/MoneySpent.xlsx',
    'feedback': 'data/retailer_feedback.xlsx',
    'ai_suggestions': 'data/supplier_ai_suggest_products.xlsx',
    'delivery_assigned': 'data/Delivery_assigned.xlsx',
    'delivery_history': 'data/DeliveryHistory.xlsx',
    'wallet_transactions': 'data/wallet_transactions.xlsx'
}
# Create data directory and Excel files if they don't exist
if not os.path.exists('data'):
    os.makedirs('data')

for file_path in EXCEL_FILES.values():
    if not os.path.exists(file_path):
        # For wallet_transactions, create with specific columns
        if file_path == EXCEL_FILES['wallet_transactions']:
            pd.DataFrame(columns=[
                'TransactionID',
                'RetailerID',
                'Amount',
                'Type',
                'Date',
                'Description'
            ]).to_excel(file_path, index=False)
        else:
            pd.DataFrame().to_excel(file_path, index=False)

# Create data directory and Excel files if they don't exist
if not os.path.exists('data'):
    os.makedirs('data')

for file_path in EXCEL_FILES.values():
    if not os.path.exists(file_path):
        pd.DataFrame().to_excel(file_path, index=False)

# Helper functions
def validate_aadhaar(number):
    return bool(re.match(r'^\d{12}$', number))

def validate_phone(number):
    return bool(re.match(r'^\d{10}$', number))

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def get_next_id(df, column='ID'):
    return df[column].max() + 1 if not df.empty else 1

def save_to_excel(data, file_name, sheet_name='Sheet1'):
    file_path = EXCEL_FILES[file_name]
    try:
        df = pd.read_excel(file_path)
    except:
        df = pd.DataFrame()
    
    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_excel(file_path, index=False)

def read_excel(file_name):
    file_path = EXCEL_FILES[file_name]
    try:
        return pd.read_excel(file_path)
    except:
        return pd.DataFrame()

def update_excel(file_name, data, condition_col, condition_val):
    file_path = EXCEL_FILES[file_name]
    try:
        df = pd.read_excel(file_path)
        df.loc[df[condition_col] == condition_val, list(data.keys())] = list(data.values())
        df.to_excel(file_path, index=False)
        return True
    except Exception as e:
        print(f"Error updating Excel: {e}")
        return False

# Routes
@app.route('/')
def home():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = {
            'RetailerName': request.form['retailer_name'],
            'ShopName': request.form['shop_name'],
            'AadhaarNumber': request.form['aadhaar'],
            'PhoneNumber': request.form['phone'],
            'Email': request.form['email'],
            'Password': request.form['password'],
            'ShopAddress': request.form['address'],
            'PinCode': request.form['pincode'],
            'LicenseProof': request.files['license'].filename if 'license' in request.files else '',
            'Role': 'Retailer'
        }
        
        # Validations
        if not validate_aadhaar(data['AadhaarNumber']):
            flash('Invalid Aadhaar number (must be 12 digits)', 'error')
            return redirect(url_for('register'))
        
        if not validate_phone(data['PhoneNumber']):
            flash('Invalid phone number (must be 10 digits)', 'error')
            return redirect(url_for('register'))
        
        if not validate_email(data['Email']):
            flash('Invalid email address', 'error')
            return redirect(url_for('register'))
        
        # Check if email already exists
        users_df = read_excel('retailer_users')
        if not users_df.empty and data['Email'] in users_df['Email'].values:
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        # Generate RetailerID
        data['RetailerID'] = str(uuid.uuid4())
        
        # Save to Excel
        save_to_excel(data, 'retailer_users')
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        users_df = read_excel('retailer_users')
        user = users_df[(users_df['Email'] == email) & (users_df['Password'] == password)]
        
        if not user.empty:
            session['retailer_id'] = user.iloc[0]['RetailerID']
            session['retailer_name'] = user.iloc[0]['RetailerName']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    retailer_id = session['retailer_id']
    
    # Get retailer data
    retailer_orders = read_excel('retailer_orders')
    retailer_orders = retailer_orders[retailer_orders['RetailerID'] == retailer_id]
    
    # Dashboard stats
    total_orders = len(retailer_orders)
    pending_orders = len(retailer_orders[retailer_orders['OrderStatus'] == 'Pending'])
    total_products = retailer_orders['Quantity'].sum() if not retailer_orders.empty else 0
    
    # Money spent
    money_spent = read_excel('money_spent')
    money_spent = money_spent[money_spent['RetailerID'] == retailer_id]
    total_money_spent = money_spent['AmountPaid'].sum() if not money_spent.empty else 0
    
    # AI suggestions - convert to list of dicts
    ai_suggestions = read_excel('ai_suggestions')
    ai_suggestions = ai_suggestions[ai_suggestions['RetailerID'] == retailer_id].head(3)
    ai_suggestions_list = ai_suggestions.to_dict('records') if not ai_suggestions.empty else []
    
    # Generate charts
    chart1 = generate_order_trend_chart(retailer_id)
    chart2 = generate_top_products_chart(retailer_id)
    
    return render_template('dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         total_products=total_products,
                         total_money_spent=total_money_spent,
                         ai_suggestions=ai_suggestions_list,  # Pass the list instead of DataFrame
                         chart1=chart1,
                         chart2=chart2)

def generate_order_trend_chart(retailer_id):
    retailer_orders = read_excel('retailer_orders')
    retailer_orders = retailer_orders[retailer_orders['RetailerID'] == retailer_id]
    
    if retailer_orders.empty:
        return None
    
    retailer_orders['OrderDate'] = pd.to_datetime(retailer_orders['OrderDate'])
    orders_by_month = retailer_orders.groupby(retailer_orders['OrderDate'].dt.to_period('M')).size()
    
    plt.figure(figsize=(8, 4))
    orders_by_month.plot(kind='line', marker='o')
    plt.title('Your Orders Trend')
    plt.xlabel('Month')
    plt.ylabel('Number of Orders')
    plt.grid(True)
    
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode('utf8')

def generate_top_products_chart(retailer_id):
    retailer_orders = read_excel('retailer_orders')
    retailer_orders = retailer_orders[retailer_orders['RetailerID'] == retailer_id]
    
    if retailer_orders.empty:
        return None
    
    top_products = retailer_orders.groupby('ProductName')['Quantity'].sum().nlargest(5)
    
    plt.figure(figsize=(8, 4))
    top_products.plot(kind='bar')
    plt.title('Your Top Products')
    plt.xlabel('Product')
    plt.ylabel('Quantity Ordered')
    plt.xticks(rotation=45)
    
    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()
    
    return base64.b64encode(img.getvalue()).decode('utf8')

@app.route('/products')
def products():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    products_df = read_excel('products')
    categories = products_df['Category'].unique() if not products_df.empty else []
    suppliers = products_df['SupplierName'].unique() if not products_df.empty else []
    
    # Apply filters
    category_filter = request.args.get('category')
    supplier_filter = request.args.get('supplier')
    search_query = request.args.get('search')
    min_price = request.args.get('min_price')
    max_price = request.args.get('max_price')
    
    filtered_products = products_df.copy()
    
    if category_filter and category_filter != 'all':
        filtered_products = filtered_products[filtered_products['Category'] == category_filter]
    
    if supplier_filter and supplier_filter != 'all':
        filtered_products = filtered_products[filtered_products['SupplierName'] == supplier_filter]
    
    if search_query:
        filtered_products = filtered_products[
            filtered_products['ProductName'].str.contains(search_query, case=False) |
            filtered_products['Description'].str.contains(search_query, case=False)
        ]
    
    if min_price:
        filtered_products = filtered_products[filtered_products['Price'] >= float(min_price)]
    
    if max_price:
        filtered_products = filtered_products[filtered_products['Price'] <= float(max_price)]
    
    return render_template('products.html', 
                         products=filtered_products.to_dict('records'),
                         categories=categories,
                         suppliers=suppliers)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    
    products_df = read_excel('products')
    product = products_df[products_df['ProductID'] == product_id].iloc[0]
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if product already in cart
    item_exists = False
    for item in session['cart']:
        if item['product_id'] == product_id:
            item['quantity'] += quantity
            item_exists = True
            break
    
    if not item_exists:
        session['cart'].append({
            'product_id': product_id,
            'product_name': product['ProductName'],
            'price': product['Price'],
            'quantity': quantity,
            'image_url': product['ImageURL']
        })
    
    session.modified = True
    flash('Product added to cart!', 'success')
    return redirect(url_for('products'))

@app.route('/cart')
def view_cart():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    cart = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart)
    
    return render_template('cart.html', cart=cart, total=total)
# Add these new routes to app.py

@app.route('/add_money', methods=['POST'])
def add_money():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    try:
        amount = float(request.form['amount'])
        if amount < 100:
            flash('Minimum amount to add is ₹100', 'error')
            return redirect(url_for('wallet'))
        
        retailer_id = session['retailer_id']
        
        # Record the transaction
        transaction_id = str(uuid.uuid4())
        transaction_data = {
            'TransactionID': transaction_id,
            'RetailerID': retailer_id,
            'Amount': amount,
            'Type': 'Credit',
            'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Description': 'Wallet top-up'
        }
        
        # Save to a new wallet_transactions Excel file
        save_to_excel(transaction_data, 'wallet_transactions')
        
        flash(f'₹{amount:.2f} added to your wallet successfully!', 'success')
    except ValueError:
        flash('Invalid amount entered', 'error')
    
    return redirect(url_for('wallet'))

# Update the wallet route to calculate balance from transactions
@app.route('/wallet')
def wallet():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    retailer_id = session['retailer_id']
    
    # Read wallet transactions
    try:
        wallet_transactions = read_excel('wallet_transactions')
        # Check if 'Type' column exists, if not create empty DataFrame
        if 'Type' not in wallet_transactions.columns:
            wallet_transactions = pd.DataFrame(columns=[
                'TransactionID', 'RetailerID', 'Amount', 'Type', 'Date', 'Description'
            ])
        wallet_transactions = wallet_transactions[wallet_transactions['RetailerID'] == retailer_id]
    except Exception as e:
        print(f"Error reading wallet transactions: {e}")
        wallet_transactions = pd.DataFrame(columns=[
            'TransactionID', 'RetailerID', 'Amount', 'Type', 'Date', 'Description'
        ])
    
    # Calculate wallet balance (sum of all credits minus debits)
    if not wallet_transactions.empty and 'Type' in wallet_transactions.columns:
        credits = wallet_transactions[wallet_transactions['Type'] == 'Credit']['Amount'].sum()
        debits = wallet_transactions[wallet_transactions['Type'] == 'Debit']['Amount'].sum()
        wallet_balance = credits - debits
    else:
        wallet_balance = 0
    
    # Read payment history (now using wallet transactions)
    if not wallet_transactions.empty and 'Type' in wallet_transactions.columns:
        payment_history = wallet_transactions[wallet_transactions['Type'] == 'Debit'].copy()
    else:
        payment_history = pd.DataFrame()
    
    # Get pending payments
    retailer_orders = read_excel('retailer_orders')
    retailer_orders = retailer_orders[retailer_orders['RetailerID'] == retailer_id]
    
    # Get orders that have payment transactions
    if not payment_history.empty and 'Description' in payment_history.columns:
        paid_orders = payment_history['Description'].str.extract(r'Payment for order (\w+)')[0].unique()
    else:
        paid_orders = []
    
    pending_orders = retailer_orders[~retailer_orders['OrderID'].isin(paid_orders)]
    pending_total = pending_orders.groupby('OrderID').apply(
        lambda x: (x['Price'] * x['Quantity']).sum()
    ).sum() if not pending_orders.empty else 0
    
    return render_template('wallet.html', 
                         payment_history=payment_history.to_dict('records'),
                         wallet_balance=wallet_balance,
                         pending_total=pending_total)

# Update the make_payment route to deduct from wallet
@app.route('/make_payment', methods=['POST'])
def make_payment():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    retailer_id = session['retailer_id']
    order_id = request.form['order_id']
    
    # Calculate amount
    retailer_orders = read_excel('retailer_orders')
    order_items = retailer_orders[(retailer_orders['RetailerID'] == retailer_id) & 
                                (retailer_orders['OrderID'] == order_id)]
    
    if order_items.empty:
        flash('No orders found to pay', 'error')
        return redirect(url_for('wallet'))
    
    amount = (order_items['Price'] * order_items['Quantity']).sum()
    
    if amount <= 0:
        flash('Invalid payment amount', 'error')
        return redirect(url_for('wallet'))
    
    # Check wallet balance
    wallet_transactions = read_excel('wallet_transactions')
    wallet_transactions = wallet_transactions[wallet_transactions['RetailerID'] == retailer_id]
    
    if not wallet_transactions.empty:
        credits = wallet_transactions[wallet_transactions['Type'] == 'Credit']['Amount'].sum()
        debits = wallet_transactions[wallet_transactions['Type'] == 'Debit']['Amount'].sum()
        wallet_balance = credits - debits
    else:
        wallet_balance = 0
    
    if wallet_balance < amount:
        flash('Insufficient wallet balance. Please add money to your wallet.', 'error')
        return redirect(url_for('wallet'))
    
    # Record the debit transaction
    transaction_id = str(uuid.uuid4())
    transaction_data = {
        'TransactionID': transaction_id,
        'RetailerID': retailer_id,
        'Amount': amount,
        'Type': 'Debit',
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Description': f'Payment for order {order_id}'
    }
    
    save_to_excel(transaction_data, 'wallet_transactions')
    
    # Also update the order status to Paid
    retailer_orders.loc[(retailer_orders['RetailerID'] == retailer_id) & 
                      (retailer_orders['OrderID'] == order_id), 'OrderStatus'] = 'Paid'
    retailer_orders.to_excel(EXCEL_FILES['retailer_orders'], index=False)
    
    flash(f'Payment of ₹{amount:.2f} successful!', 'success')
    return redirect(url_for('wallet'))

@app.route('/place_order', methods=['POST'])
def place_order():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    retailer_id = session['retailer_id']
    cart = session.get('cart', [])
    
    if not cart:
        flash('Your cart is empty!', 'error')
        return redirect(url_for('products'))
    
    # Calculate total order amount
    total_amount = sum(item['price'] * item['quantity'] for item in cart)
    
    # Check wallet balance
    wallet_transactions = read_excel('wallet_transactions')
    wallet_transactions = wallet_transactions[wallet_transactions['RetailerID'] == retailer_id]
    
    if not wallet_transactions.empty:
        credits = wallet_transactions[wallet_transactions['Type'] == 'Credit']['Amount'].sum()
        debits = wallet_transactions[wallet_transactions['Type'] == 'Debit']['Amount'].sum()
        wallet_balance = credits - debits
    else:
        wallet_balance = 0
    
    if wallet_balance < total_amount:
        flash(f'Insufficient wallet balance. Your order total is ₹{total_amount:.2f} but you only have ₹{wallet_balance:.2f}. Please add money to your wallet.', 'error')
        return redirect(url_for('view_cart'))
    
    order_id = str(uuid.uuid4())
    order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save to retailer_orders.xlsx
    for item in cart:
        retailer_order_data = {
            'OrderID': order_id,
            'RetailerID': retailer_id,
            'ProductID': item['product_id'],
            'ProductName': item['product_name'],
            'Quantity': item['quantity'],
            'Price': item['price'],
            'OrderStatus': 'Pending',
            'OrderDate': order_date
        }
        save_to_excel(retailer_order_data, 'retailer_orders')
    
    # Save to Orders.xlsx (global)
    for item in cart:
        order_data = {
            'OrderID': order_id,
            'RetailerID': retailer_id,
            'ProductID': item['product_id'],
            'Quantity': item['quantity'],
            'OrderStatus': 'Pending',
            'DeliveryAssigned': '',
            'ExpectedDeliveryDate': (datetime.now() + pd.Timedelta(days=3)).strftime('%Y-%m-%d')
        }
        save_to_excel(order_data, 'orders')
    
    # Save to delivery_status.xlsx
    delivery_status_data = {
        'OrderID': order_id,
        'DeliveryPerson': '',
        'Status': 'Pending',
        'PickedDate': '',
        'DeliveredDate': ''
    }
    save_to_excel(delivery_status_data, 'delivery_status')
    
    # Deduct from wallet
    transaction_id = str(uuid.uuid4())
    transaction_data = {
        'TransactionID': transaction_id,
        'RetailerID': retailer_id,
        'Amount': total_amount,
        'Type': 'Debit',
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Description': f'Payment for order {order_id}'
    }
    save_to_excel(transaction_data, 'wallet_transactions')
    
    # Also save to money_spent for backward compatibility
    payment_data = {
        'RetailerID': retailer_id,
        'OrderID': order_id,
        'AmountPaid': total_amount,
        'PaymentDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Status': 'Paid'
    }
    save_to_excel(payment_data, 'money_spent')
    
    # Clear cart
    session.pop('cart', None)
    
    flash(f'Order placed successfully! ₹{total_amount:.2f} deducted from your wallet.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/track_orders')
def track_orders():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    retailer_id = session['retailer_id']
    
    # Get retailer's orders
    retailer_orders = read_excel('retailer_orders')
    retailer_orders = retailer_orders[retailer_orders['RetailerID'] == retailer_id]
    
    # Get unique order IDs
    order_ids = retailer_orders['OrderID'].unique()
    
    # Get delivery status for each order
    delivery_status = read_excel('delivery_status')
    orders_with_status = []
    
    for order_id in order_ids:
        order_products = retailer_orders[retailer_orders['OrderID'] == order_id]
        status = delivery_status[delivery_status['OrderID'] == order_id]
        
        if not status.empty:
            status = status.iloc[0]
            orders_with_status.append({
                'order_id': order_id,
                'products': order_products.to_dict('records'),
                'delivery_person': status['DeliveryPerson'],
                'status': status['Status'],
                'expected_delivery': order_products.iloc[0]['OrderDate']  # Simplified
            })
    
    return render_template('track_orders.html', orders=orders_with_status)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        feedback_data = {
            'RetailerID': session['retailer_id'],
            'OrderID': request.form['order_id'],
            'FeedbackType': request.form['feedback_type'],
            'Message': request.form['message'],
            'DateSubmitted': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_to_excel(feedback_data, 'feedback')
        flash('Feedback submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get retailer's orders for dropdown
    retailer_orders = read_excel('retailer_orders')
    retailer_orders = retailer_orders[retailer_orders['RetailerID'] == session['retailer_id']]
    order_ids = retailer_orders['OrderID'].unique()
    
    return render_template('feedback.html', order_ids=order_ids)



@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'retailer_id' not in session:
        return redirect(url_for('login'))
    
    retailer_id = session['retailer_id']
    users_df = read_excel('retailer_users')
    user = users_df[users_df['RetailerID'] == retailer_id].iloc[0]
    
    if request.method == 'POST':
        # Update profile
        update_data = {
            'PhoneNumber': request.form['phone'],
            'Email': request.form['email'],
            'ShopAddress': request.form['address'],
            'PinCode': request.form['pincode']
        }
        
        if 'password' in request.form and request.form['password']:
            update_data['Password'] = request.form['password']
        
        if update_excel('retailer_users', update_data, 'RetailerID', retailer_id):
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Error updating profile', 'error')
    
    return render_template('profile.html', user=user.to_dict())

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)