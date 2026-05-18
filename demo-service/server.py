"""Demo e-commerce API for testing. Supports two environments via --env-name."""
import argparse
import time
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Demo E-Commerce API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

ENV_NAME = "local"
VALID_CREDENTIALS = {"admin": "123456"}
PRODUCTS = [
    {"id": 1, "name": "机械键盘", "price": 299, "stock": 50},
    {"id": 2, "name": "无线鼠标", "price": 99, "stock": 200},
    {"id": 3, "name": "显示器支架", "price": 159, "stock": 30},
    {"id": 4, "name": "Type-C 数据线", "price": 29, "stock": 500},
    {"id": 5, "name": "笔记本散热架", "price": 79, "stock": 80},
]
ORDERS = [
    {"id": 1, "product_id": 1, "quantity": 2, "status": "paid", "total": 598},
    {"id": 2, "product_id": 3, "quantity": 1, "status": "shipped", "total": 159},
    {"id": 3, "product_id": 5, "quantity": 3, "status": "pending", "total": 237},
]

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/v1/health")
def health():
    return {"status": "ok", "env": ENV_NAME, "timestamp": time.time()}

@app.post("/api/v1/login")
def login(req: LoginRequest):
    if req.username not in VALID_CREDENTIALS:
        raise HTTPException(status_code=401, detail="Invalid username")
    if VALID_CREDENTIALS[req.username] != req.password:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {"token": f"mock-jwt-{req.username}-{ENV_NAME}", "username": req.username}

@app.get("/api/v1/products")
def list_products(keyword: str = Query(default="", description="Search keyword")):
    if keyword:
        return {"products": [p for p in PRODUCTS if keyword.lower() in p["name"].lower()], "total": len([p for p in PRODUCTS if keyword.lower() in p["name"].lower()]), "env": ENV_NAME}
    return {"products": PRODUCTS, "total": len(PRODUCTS), "env": ENV_NAME}

@app.get("/api/v1/products/{product_id}")
def get_product(product_id: int):
    if product_id == 0:
        raise HTTPException(status_code=500, detail="Internal server error: database connection lost")
    for p in PRODUCTS:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

@app.get("/api/v1/orders")
def list_orders(status: str = Query(default="", description="Filter by status")):
    if status:
        filtered = [o for o in ORDERS if o["status"] == status]
        return {"orders": filtered, "total": len(filtered), "env": ENV_NAME}
    return {"orders": ORDERS, "total": len(ORDERS), "env": ENV_NAME}

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-name", default="local")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()
    ENV_NAME = args.env_name
    if args.env_name == "staging":
        VALID_CREDENTIALS["admin"] = "staging123"
    uvicorn.run(app, host="0.0.0.0", port=args.port)
