# Admin Account Setup

## Creating an Admin User

To create an admin user for the hospital management system, run:

```bash
python manage.py create_admin
```

This will create an admin user with default credentials:
- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@hospital.com`

### Custom Credentials

You can specify custom credentials:

```bash
python manage.py create_admin --username myadmin --password mypassword123 --email myadmin@hospital.com
```

### Using Django's Built-in Command

Alternatively, you can use Django's built-in `createsuperuser` command:

```bash
python manage.py createsuperuser
```

This will prompt you to enter username, email, and password interactively.

## Important Notes

⚠️ **Security Warning:** The default password (`admin123`) is for development only. 
**Always change the password after first login in production environments!**

## After Creating Admin

1. Run migrations (if not already done):
   ```bash
   python manage.py migrate
   ```

2. Create admin user (using one of the methods above)

3. Start the development server:
   ```bash
   python manage.py runserver
   ```

4. Login at: `http://localhost:8000/login/`

## Creating Patient Accounts

To create patient accounts that can login:

1. Create a regular Django User account (not staff)
2. Create or link a Patient record to that User account via the `user` field
3. The patient can then login using their User credentials

You can do this through:
- Django Admin interface (after logging in as admin)
- Custom management command (to be created)
- Programmatically in your code


