document.addEventListener('DOMContentLoaded', () => {
    const initialView = document.getElementById('initial-view');
    const registerView = document.getElementById('register-view');
    const loginView = document.getElementById('login-view');
    const operationsView = document.getElementById('operations-view');
    const transactionInputView = document.getElementById('transaction-input-view');
    const transactionResultView = document.getElementById('transaction-result-view');

    const showRegisterButton = document.getElementById('show-register');
    const showLoginButton = document.getElementById('show-login');
    const backButtons = document.querySelectorAll('.back-button');
    const logoutButton = document.getElementById('logout-button');

    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    const registerMessage = document.getElementById('register-message');
    const loginMessage = document.getElementById('login-message');
    const loggedInUsernameSpan = document.getElementById('logged-in-username');
    const checkBalanceButton = document.getElementById('check-balance-button');
    const balanceDisplay = document.getElementById('balance-display');
    const operationMessage = document.getElementById('operation-message');

    const transactionTypeTitle = document.getElementById('transaction-type-title');
    const transactionInputLabel = document.getElementById('transaction-input-label');
    const transactionAmountInput = document.getElementById('transaction-amount');
    const transactionInputMessage = document.getElementById('transaction-input-message');
    const submitTransactionButton = document.getElementById('submit-transaction');
    const keypadKeys = document.querySelectorAll('.keypad-key');
    const backToOpsButtons = document.querySelectorAll('.back-to-ops');

    let accessToken = null; // Variable to store the access token
    let userAccounts = []; // Variable to store user's accounts
    let selectedAccountId = null; // Variable to store the selected account ID (for simplicity, the first account)
    let currentTransactionType = null; // To track the current transaction (deposit, withdraw, etc.)

    // Function to show a specific view and hide others
    function showView(viewToShow) {
        const views = [initialView, registerView, loginView, operationsView, transactionInputView, transactionResultView];
        views.forEach(view => {
            if (view === viewToShow) {
                view.style.display = 'flex'; // Use flex to center content
            } else {
                view.style.display = 'none';
            }
        });
         // Clear keypad input and message when changing views
        if (viewToShow !== transactionInputView) {
             transactionAmountInput.value = '';
             transactionInputMessage.textContent = '';
        }
         // Clear operation message when leaving operations view
        if (viewToShow !== operationsView) {
            operationMessage.textContent = '';
        }
         // Clear result message when leaving result view
        if (viewToShow !== transactionResultView) {
            resultMessage.textContent = '';
        }
    }

    // Event listeners for initial choice buttons
    showRegisterButton.addEventListener('click', () => {
        showView(registerView);
        registerMessage.textContent = ''; // Clear messages
        registerForm.reset(); // Clear form
    });

    showLoginButton.addEventListener('click', () => {
        showView(loginView);
        loginMessage.textContent = ''; // Clear messages
        loginForm.reset(); // Clear form
    });

    // Event listeners for back buttons
    backButtons.forEach(button => {
        button.addEventListener('click', () => {
            showView(initialView);
        });
    });

     // Event listeners for back to operations buttons
    backToOpsButtons.forEach(button => {
        button.addEventListener('click', () => {
            showView(operationsView);
             balanceDisplay.textContent = ''; // Clear balance display when going back
        });
    });

    // Event listener for logout button
    logoutButton.addEventListener('click', () => {
        // Clear token and account data
        accessToken = null;
        userAccounts = [];
        selectedAccountId = null;
        console.log('Logout clicked, token and account cleared');
        showView(initialView);
         loggedInUsernameSpan.textContent = ''; // Clear username display
         balanceDisplay.textContent = ''; // Clear balance display
    });

    // Handle Registration Form Submission
    registerForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        registerMessage.textContent = 'Registering...';
        registerMessage.style.color = '#333'; // Default color

        const formData = new FormData(registerForm);
        const userData = Object.fromEntries(formData.entries());

        console.log('Register data:', userData);

        try {
            const response = await fetch('/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const result = await response.json();

            if (response.ok) {
                registerMessage.textContent = 'Registration successful! Please login.';
                 registerMessage.style.color = '#28a745'; // Green color for success
                registerForm.reset(); // Clear form on success
                // Optionally, redirect to login view after a delay
                 setTimeout(() => { showView(loginView); }, 2000);
            } else {
                // Display error message from backend
                registerMessage.textContent = `Registration failed: ${result.error || response.statusText}`;
                 registerMessage.style.color = '#dc3545'; // Red color for error
            }
        } catch (error) {
            registerMessage.textContent = `Registration failed: ${error.message}`;
            registerMessage.style.color = '#dc3545'; // Red color for error
            console.error('Registration error:', error);
        }
    });

    // Handle Login Form Submission
    loginForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        loginMessage.textContent = 'Logging in...';
        loginMessage.style.color = '#333'; // Default color

        const formData = new FormData(loginForm);
        const loginData = Object.fromEntries(formData.entries());

        console.log('Login data:', loginData);

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginData)
            });

            const result = await response.json();

            if (response.ok) {
                // Store the access token
                accessToken = result.access_token;
                console.log('Login successful', result);
                loginMessage.textContent = 'Login successful!';
                 loginMessage.style.color = '#28a745'; // Green color for success
                loginForm.reset(); // Clear form on success

                loggedInUsernameSpan.textContent = loginData.username; // Display entered username for now

                // Fetch user accounts after successful login
                await fetchUserAccounts();

                showView(operationsView); // Show ATM operations view

            } else {
                // Display error message from backend
                 loginMessage.textContent = `Login failed: ${result.error || response.statusText}`;
                 loginMessage.style.color = '#dc3545'; // Red color for error
            }
        } catch (error) {
            loginMessage.textContent = `Login failed: ${error.message}`;
            loginMessage.style.color = '#dc3545'; // Red color for error
            console.error('Login error:', error);
        }
    });

    // Function to fetch user's accounts
    async function fetchUserAccounts() {
        if (!accessToken) {
            console.error('No access token available to fetch accounts.');
             operationMessage.textContent = 'Error: Not authenticated.';
             operationMessage.style.color = '#dc3545';
            return;
        }
        try {
            const response = await fetch('/accounts', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                userAccounts = result.accounts;
                console.log('Fetched user accounts:', userAccounts);
                if (userAccounts.length > 0) {
                    // For simplicity, select the first account
                    selectedAccountId = userAccounts[0].id;
                    console.log('Selected account ID:', selectedAccountId);
                     operationMessage.textContent = 'Accounts loaded. Choose an operation.';
                     operationMessage.style.color = '#28a745';
                } else {
                    console.warn('User has no accounts.');
                     operationMessage.textContent = 'No accounts found for this user.';
                     operationMessage.style.color = '#dc3545';
                    // TODO: Handle case where user has no accounts - maybe redirect or show a specific message
                }
            } else {
                console.error('Failed to fetch user accounts:', result.error || response.statusText);
                 operationMessage.textContent = `Failed to load accounts: ${result.error || response.statusText}`;
                 operationMessage.style.color = '#dc3545';
            }
        } catch (error) {
            console.error('Error fetching user accounts:', error);
             operationMessage.textContent = `Error loading accounts: ${error.message}`;
             operationMessage.style.color = '#dc3545';
        }
    }

    // Handle Check Balance Button Click
    checkBalanceButton.addEventListener('click', async () => {
        if (!selectedAccountId || !accessToken) {
            balanceDisplay.textContent = 'Please login and ensure you have an account.';
            balanceDisplay.style.color = '#dc3545'; // Red color for error
            return;
        }

        balanceDisplay.textContent = 'Fetching balance...';
        balanceDisplay.style.color = '#333'; // Default color

        try {
            const response = await fetch(`/accounts/${selectedAccountId}/balance`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`
                }
            });

            const result = await response.json();

            if (response.ok) {
                balanceDisplay.textContent = `Balance: $${result.balance.toFixed(2)}`;
                 balanceDisplay.style.color = '#28a745'; // Green color for success
            } else {
                balanceDisplay.textContent = `Failed to fetch balance: ${result.error || response.statusText}`;
                balanceDisplay.style.color = '#dc3545'; // Red color for error
            }
        } catch (error) {
            balanceDisplay.textContent = `Error fetching balance: ${error.message}`;
            balanceDisplay.style.color = '#dc3545'; // Red color for error
            console.error('Error fetching balance:', error);
        }
    });

     // Handle Transaction Button Clicks (Deposit, Withdraw, etc.)
    document.querySelectorAll('.transaction-button').forEach(button => {
        button.addEventListener('click', () => {
            currentTransactionType = button.getAttribute('data-transaction-type');
            transactionTypeTitle.textContent = `${currentTransactionType.replace('-', ' ').charAt(0).toUpperCase() + currentTransactionType.slice(1).replace('-', ' ')} Amount`;
            transactionInputLabel.textContent = `Enter amount for ${currentTransactionType}:`;
            transactionAmountInput.value = ''; // Clear previous input
            transactionInputMessage.textContent = ''; // Clear previous message
            showView(transactionInputView);
        });
    });

    // Handle Keypad Button Clicks
    keypadKeys.forEach(key => {
        key.addEventListener('click', () => {
            const value = key.getAttribute('data-value');
            const currentValue = transactionAmountInput.value;

            if (value === 'CLEAR') {
                transactionAmountInput.value = '';
            } else if (value === 'ENTER') {
                // The ENTER button will trigger the transaction submission
                submitTransactionButton.click(); // Simulate click on submit button
            } else if (value === '.') {
                 // Prevent adding multiple decimal points
                 if (!currentValue.includes('.')) {
                     transactionAmountInput.value += value;
                 }
             } else {
                transactionAmountInput.value += value;
            }
             transactionInputMessage.textContent = ''; // Clear any previous input message on new input
        });
    });

     // Handle Transaction Submission (triggered by ENTER keypad button or Submit button click)
     submitTransactionButton.addEventListener('click', async () => {
         const amount = parseFloat(transactionAmountInput.value);

         if (isNaN(amount) || amount <= 0) {
             transactionInputMessage.textContent = 'Please enter a valid positive amount.';
             transactionInputMessage.style.color = '#dc3545';
             return;
         }

         if (!selectedAccountId || !accessToken) {
             transactionInputMessage.textContent = 'Error: Not logged in or no account available.';
              transactionInputMessage.style.color = '#dc3545';
             return;
         }

         transactionInputMessage.textContent = 'Processing...';
         transactionInputMessage.style.color = '#333';

         // TODO: Implement the actual API call based on currentTransactionType
         console.log(`Attempting ${currentTransactionType} for amount ${amount} on account ${selectedAccountId}`);

         // For Deposit, call the deposit endpoint
         if (currentTransactionType === 'deposit') {
             try {
                 const response = await fetch(`/accounts/${selectedAccountId}/deposit`, {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                         'Authorization': `Bearer ${accessToken}`
                     },
                     body: JSON.stringify({ amount: amount })
                 });

                 const result = await response.json();
                 const resultMessageElement = document.getElementById('result-message');

                 if (response.ok) {
                     resultMessageElement.textContent = `Deposit successful. New balance: $${result.balance_after.toFixed(2)}`;
                      resultMessageElement.style.color = '#28a745';
                 } else {
                     resultMessageElement.textContent = `Deposit failed: ${result.error || response.statusText}`;
                      resultMessageElement.style.color = '#dc3545';
                 }
                 showView(transactionResultView);
             } catch (error) {
                 const resultMessageElement = document.getElementById('result-message');
                 resultMessageElement.textContent = `Error during deposit: ${error.message}`;
                  resultMessageElement.style.color = '#dc3545';
                 console.error('Deposit error:', error);
                  showView(transactionResultView);
             }
         } else if (currentTransactionType === 'withdraw') {
             // Implement Withdrawal logic
              try {
                 const response = await fetch(`/accounts/${selectedAccountId}/withdraw`, {
                     method: 'POST',
                     headers: {
                         'Content-Type': 'application/json',
                         'Authorization': `Bearer ${accessToken}`
                     },
                     body: JSON.stringify({ amount: amount })
                 });

                 const result = await response.json();
                 const resultMessageElement = document.getElementById('result-message');

                 if (response.ok) {
                     resultMessageElement.textContent = `Withdrawal successful. New balance: $${result.balance_after.toFixed(2)}`;
                      resultMessageElement.style.color = '#28a745';
                 } else {
                     // Handle specific insufficient funds error or general failure
                      const errorMessage = result.error || response.statusText;
                      if (errorMessage === 'Insufficient funds') {
                         resultMessageElement.textContent = 'Withdrawal failed: Insufficient funds.';
                     } else {
                         resultMessageElement.textContent = `Withdrawal failed: ${errorMessage}`;
                     }
                      resultMessageElement.style.color = '#dc3545';
                 }
                 showView(transactionResultView);
             } catch (error) {
                 const resultMessageElement = document.getElementById('result-message');
                 resultMessageElement.textContent = `Error during withdrawal: ${error.message}`;
                  resultMessageElement.style.color = '#dc3545';
                 console.error('Withdrawal error:', error);
                  showView(transactionResultView);
             }
         } else if (currentTransactionType === 'transfer') {
             // TODO: Implement Transfer logic (requires more input fields)
              transactionInputMessage.textContent = 'Transfer not yet implemented.';
              transactionInputMessage.style.color = '#dc3545';
         } else if (currentTransactionType === 'mini-statement') {
             // TODO: Implement Mini Statement logic
              transactionInputMessage.textContent = 'Mini Statement not yet implemented.';
              transactionInputMessage.style.color = '#dc3545';
         }
     });

    // Initially show the initial view
    showView(initialView);
}); 