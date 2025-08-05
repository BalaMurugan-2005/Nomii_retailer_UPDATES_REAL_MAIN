import os
import random
from faker import Faker
import pandas as pd
from datetime import datetime, timedelta

# Create 'data' directory if it doesn't exist
os.makedirs("data", exist_ok=True)

fake = Faker()

# 1. retailer_users.xlsx
retailer_users = pd.DataFrame([{
    "RetailerID": f"R{1000+i}",
    "RetailerName": fake.name(),
    "ShopName": fake.company(),
    "AadhaarNumber": fake.unique.random_number(digits=12),
    "PhoneNumber": fake.phone_number(),
    "Email": fake.email(),
    "Password": fake.password(),
    "ShopAddress": fake.address().replace('\n', ', '),
    "PinCode": fake.postcode(),
    "LicenseProof": f"license_{1000+i}.jpg",
    "Role": "Retailer"
} for i in range(10)])

# 2. Products.xlsx
products = pd.DataFrame([{
    "ProductID": f"P{2000+i}",
    "ProductName": fake.word().capitalize(),
    "ImageURL": fake.image_url(),
    "Price": round(random.uniform(50, 1000), 2),
    "Description": fake.sentence(),
    "Category": random.choice(["Grocery", "Electronics", "Clothing", "Stationery"]),
    "SupplierName": fake.company(),
    "StockQuantity": random.randint(10, 100)
} for i in range(10)])

# 3. retailer_orders.xlsx
retailer_orders = pd.DataFrame([{
    "OrderID": f"O{3000+i}",
    "RetailerID": random.choice(retailer_users["RetailerID"]),
    "ProductID": random.choice(products["ProductID"]),
    "ProductName": random.choice(products["ProductName"]),
    "Quantity": random.randint(1, 10),
    "Price": round(random.uniform(100, 5000), 2),
    "OrderStatus": random.choice(["Pending", "Shipped", "Delivered"]),
    "OrderDate": fake.date_this_year()
} for i in range(10)])

# 4. Orders.xlsx
orders = pd.DataFrame([{
    "OrderID": retailer_orders.iloc[i]["OrderID"],
    "RetailerID": retailer_orders.iloc[i]["RetailerID"],
    "ProductID": retailer_orders.iloc[i]["ProductID"],
    "Quantity": retailer_orders.iloc[i]["Quantity"],
    "OrderStatus": retailer_orders.iloc[i]["OrderStatus"],
    "DeliveryAssigned": random.choice(["Yes", "No"]),
    "ExpectedDeliveryDate": fake.date_between(start_date="today", end_date="+5d")
} for i in range(10)])

# 5. deliverystatus.xlsx
deliverystatus = pd.DataFrame([{
    "OrderID": orders.iloc[i]["OrderID"],
    "DeliveryPerson": fake.name(),
    "Status": random.choice(["Picked", "In Transit", "Delivered"]),
    "PickedDate": fake.date_between(start_date="-5d", end_date="today"),
    "DeliveredDate": fake.date_between(start_date="today", end_date="+2d") if random.choice([True, False]) else None
} for i in range(10)])

# 6. MoneySpent.xlsx
money_spent = pd.DataFrame([{
    "RetailerID": random.choice(retailer_users["RetailerID"]),
    "OrderID": random.choice(retailer_orders["OrderID"]),
    "AmountPaid": round(random.uniform(200, 5000), 2),
    "PaymentDate": fake.date_this_year(),
    "Status": random.choice(["Paid", "Pending"])
} for i in range(10)])

# 7. retailer_feedback.xlsx
feedback = pd.DataFrame([{
    "RetailerID": random.choice(retailer_users["RetailerID"]),
    "OrderID": random.choice(retailer_orders["OrderID"]),
    "FeedbackType": random.choice(["Complaint", "Suggestion", "Appreciation"]),
    "Message": fake.sentence(),
    "DateSubmitted": fake.date_this_year()
} for i in range(10)])

# 8. supplier_ai_suggest_products.xlsx
ai_suggestions = pd.DataFrame([{
    "RetailerID": random.choice(retailer_users["RetailerID"]),
    "SuggestedProduct": fake.word().capitalize(),
    "Reason": fake.sentence(),
    "DateSuggested": fake.date_this_year()
} for i in range(10)])

# 9. Delivery_assigned.xlsx
delivery_assigned = pd.DataFrame([{
    "OrderID": random.choice(orders["OrderID"]),
    "DeliveryPerson": fake.name(),
    "AssignmentDate": fake.date_this_year()
} for i in range(10)])

# 10. DeliveryHistory.xlsx
delivery_history = pd.DataFrame([{
    "OrderID": random.choice(orders["OrderID"]),
    "RetailerID": random.choice(retailer_users["RetailerID"]),
    "ProductID": random.choice(products["ProductID"]),
    "DeliveredOn": fake.date_between(start_date="-10d", end_date="today"),
    "Quantity": random.randint(1, 10),
    "DeliveryStatus": random.choice(["Delivered", "Failed", "Pending"])
} for i in range(10)])

# Save all to files in 'data' folder
retailer_users.to_excel("data/retailer_users.xlsx", index=False)
products.to_excel("data/Products.xlsx", index=False)
retailer_orders.to_excel("data/retailer_orders.xlsx", index=False)
orders.to_excel("data/Orders.xlsx", index=False)
money_spent.to_excel("data/MoneySpent.xlsx", index=False)
deliverystatus.to_excel("data/deliverystatus.xlsx", index=False)
feedback.to_excel("data/retailer_feedback.xlsx", index=False)
ai_suggestions.to_excel("data/supplier_ai_suggest_products.xlsx", index=False)
delivery_assigned.to_excel("data/Delivery_assigned.xlsx", index=False)
delivery_history.to_excel("data/DeliveryHistory.xlsx", index=False)
