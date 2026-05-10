# import os

# # Danh sách tên các file CSV (bỏ đuôi .csv)
# tables = [
#     "geography", "products", "customers", "promotions", 
#     "orders", "order_items", "payments", "shipments", 
#     "returns", "reviews", "inventory", "web_traffic", "sales"
# ]

# # Đường dẫn đến thư mục staging
# output_dir = "models/staging"
# os.makedirs(output_dir, exist_ok=True)

# for table in tables:
#     # Nội dung chuẩn của một file staging
#     sql_content = f"""WITH source AS (
#     SELECT * FROM {{{{ ref('{table}') }}}}
# ),

# renamed AS (
#     SELECT 
#         * -- Tạm thời lấy tất cả, bạn sẽ vào sửa hàm CAST() sau nếu cần
#     FROM source
# )

# SELECT * FROM renamed
# """
#     # Tạo và ghi file
#     file_path = os.path.join(output_dir, f"stg_{table}.sql")
#     with open(file_path, "w", encoding="utf-8") as f:
#         f.write(sql_content)
        
#     print(f"Đã tạo thành công: {file_path}")

# print("Hoàn tất!")