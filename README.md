<<<<<<< HEAD
# Brainwave_Matrix_Intern
=======
# ATM Interface

A Flask-based API for an ATM interface, allowing users to perform various banking operations such as deposits, withdrawals, and transfers.

## Features

- User management (create, retrieve, update)
- Account operations (balance check, deposit, withdraw, transfer)
- Transaction categorization
- Password reset functionality
- Rate limiting
- Swagger/OpenAPI documentation

## Architecture

The project is structured as follows:

- **models/**: Contains Pydantic models for data validation.
- **services/**: Contains business logic for ATM operations.
- **utils/**: Contains utility functions for authentication, rate limiting, etc.
- **db/**: Contains database configuration and connection logic.
- **tests/**: Contains test cases for the application.

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd atm_interface
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Create a `.env` file in the project root.
   - Add the following variables:
     ```
     SUPABASE_URL=your_supabase_url
     SUPABASE_KEY=your_supabase_key
     ```

5. Run the Flask application:
   ```bash
   python main.py
   ```

## Usage

- Access the API at `http://localhost:5000`.
- View the Swagger documentation at `http://localhost:5000/api/docs`.

## API Endpoints

- **User Management:**
  - `POST /users`: Create a new user.
  - `GET /users/<user_id>`: Retrieve user details.

- **Account Operations:**
  - `GET /accounts/<account_id>/balance`: Check account balance.
  - `POST /accounts/<account_id>/deposit`: Deposit funds.
  - `POST /accounts/<account_id>/withdraw`: Withdraw funds.
  - `POST /accounts/transfer`: Transfer funds between accounts.

- **Password Reset:**
  - `POST /auth/reset-password/request`: Request a password reset token.
  - `POST /auth/reset-password/reset`: Reset the password using a token.

## Testing

Run the tests using pytest:

```bash
pytest
```

## Deployment

For production deployment, use a WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.
>>>>>>> master
