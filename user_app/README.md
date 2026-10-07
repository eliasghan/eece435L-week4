# Lab 5 - Postman and APIs

EECE 435L Software Tools Lab, Fall 2025-2026
Author: Elias Ghanem

A Flask REST API that adds, reads, updates and deletes users stored in a SQLite
database, tested with a Postman collection.

## Setup

```bash
cd user_app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Running `app.py` creates `database.db` (if it does not exist) and starts the
server on `http://127.0.0.1:5000`.

## API endpoints

| Method | Endpoint                       | Database function | Description         |
|--------|--------------------------------|-------------------|---------------------|
| GET    | `/api/users`                   | `get_users`       | List all users      |
| GET    | `/api/users/<user_id>`         | `get_user_by_id`  | Get one user        |
| POST   | `/api/users/add`               | `insert_user`     | Add a user          |
| PUT    | `/api/users/update`            | `update_user`     | Update a user       |
| DELETE | `/api/users/delete/<user_id>`  | `delete_user`     | Delete a user       |

Example body for `POST /api/users/add`:

```json
{
    "name": "John Doe",
    "email": "jondoe@gamil.com",
    "phone": "067765434567",
    "address": "John Doe Street, Innsbruck",
    "country": "Austria"
}
```

`PUT /api/users/update` takes the same fields plus `user_id`.

## Postman

The `postman/` folder contains:

- `Flask user app.postman_collection.json`: the **Flask user app** collection with
  one request per endpoint and a saved example response for each.
- `Flask user app.postman_environment.json`: the **Flask user app - Local**
  environment defining `base_url = http://127.0.0.1:5000`, used by every request
  as `{{base_url}}`.

To use them, open Postman, click **Import**, select both files, then choose the
**Flask user app - Local** environment in the top right before sending requests.
Run the requests in order on an empty database so the IDs match the examples.

## Git workflow

1. The SQLite database layer was committed on `main`.
2. A `rest-api` branch was created to add the Flask endpoints and Postman files.
3. After testing, `rest-api` was merged back into `main`.
