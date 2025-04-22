# MCP Browser Automation Examples

This document provides example commands for browser automation using the Model Context Protocol (MCP).

## Example 1: Basic Login Flow

**Task**: Login to WebDriver University portal with provided credentials.

```javascript
go to https://webdriveruniversity.com/Login-Portal/index.html  
enter the username as Red Dragon, password as dummy_password 
and click login button
```

**Steps**:
1. Navigate to login page
2. Enter username: "Red Dragon"
3. Enter password: "dummy_password"
4. Click login button

## Example 2: E-Commerce Product Selection

**Task**: Login to Sauce Demo and add specific items to cart using browser snapshot.

```javascript
// First Method
go to https://www.saucedemo.com/ 
login with standar_user and secret_sauce
buy me a jacket and a backpack

// Alternative Method with Snapshot
use browser_snapshot tool action and get the current browser data
and based on that data buy me a jacket and a backpack
```

**Steps**:
1. Navigate to Sauce Demo
2. Login with credentials:
   - Username: standard_user
   - Password: secret_sauce
3. Add items to cart:
   - Sauce Labs Fleece Jacket
   - Sauce Labs Backpack

## Example 3: Complete Checkout Flow

**Task**: Full e-commerce flow including checkout process.

```javascript
go to https://www.saucedemo.com/ 
login with standar_user and secret_sauce
buy me a jacket and a backpack
click the cart icon and check if the required products are listed in the page
and checkout 

// Checkout Information
firstname: Joe
lastname: Goldberg
postal_code: 00001

proceed to the final page and check the total price and click finish
```

**Steps**:
1. Complete login and product selection
2. Verify cart contents
3. Enter shipping information:
   - First Name: Joe
   - Last Name: Goldberg
   - Postal Code: 00001
4. Review total price
5. Complete checkout

---

**Note**: These examples demonstrate various automation scenarios using MCP tools. Refer to the README.md for detailed tool documentation.