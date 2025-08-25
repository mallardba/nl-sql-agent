
-- Comprehensive MySQL 8 schema & seed data for analytics/agent testing
-- Safe to run multiple times (drops first). Uses only SELECT in typical queries.

SET NAMES utf8mb4;
SET time_zone = '+00:00';

/* =========================
   DROP (for idempotency)
   ========================= */
DROP TABLE IF EXISTS returns;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS promotions;
DROP TABLE IF EXISTS inventories;
DROP TABLE IF EXISTS product_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS channels;

DROP VIEW IF EXISTS v_monthly_sales;
DROP VIEW IF EXISTS v_product_revenue;
DROP VIEW IF EXISTS v_customer_ltv;

/* =========================
   DIMENSIONS
   ========================= */

CREATE TABLE regions (
  id TINYINT PRIMARY KEY,
  name VARCHAR(32) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE channels (
  id TINYINT PRIMARY KEY,
  name VARCHAR(32) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE customers (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255),
  region_id TINYINT NOT NULL,
  created_at DATE NOT NULL,
  vip BOOLEAN NOT NULL DEFAULT 0,
  CONSTRAINT fk_customer_region FOREIGN KEY (region_id) REFERENCES regions(id),
  CONSTRAINT uq_customer_email UNIQUE (email)
) ENGINE=InnoDB;

CREATE TABLE employees (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  role ENUM('AE','AM','SE','SUPPORT') NOT NULL,
  region_id TINYINT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT 1,
  CONSTRAINT fk_emp_region FOREIGN KEY (region_id) REFERENCES regions(id)
) ENGINE=InnoDB;

CREATE TABLE categories (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL UNIQUE,
  parent_id INT NULL,
  CONSTRAINT fk_cat_parent FOREIGN KEY (parent_id) REFERENCES categories(id)
) ENGINE=InnoDB;

CREATE TABLE products (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  category_id INT NOT NULL,
  sku VARCHAR(64) NOT NULL UNIQUE,
  price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
  active BOOLEAN NOT NULL DEFAULT 1,
  created_at DATE NOT NULL,
  CONSTRAINT fk_prod_cat FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

CREATE TABLE tags (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE product_tags (
  product_id INT NOT NULL,
  tag_id INT NOT NULL,
  PRIMARY KEY (product_id, tag_id),
  CONSTRAINT fk_pt_prod FOREIGN KEY (product_id) REFERENCES products(id),
  CONSTRAINT fk_pt_tag FOREIGN KEY (tag_id) REFERENCES tags(id)
) ENGINE=InnoDB;

CREATE TABLE inventories (
  warehouse VARCHAR(32) NOT NULL,
  product_id INT NOT NULL,
  on_hand INT NOT NULL DEFAULT 0 CHECK (on_hand >= 0),
  PRIMARY KEY (warehouse, product_id),
  CONSTRAINT fk_inv_prod FOREIGN KEY (product_id) REFERENCES products(id)
) ENGINE=InnoDB;

CREATE TABLE promotions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(128) NOT NULL,
  discount_pct DECIMAL(5,2) NOT NULL CHECK (discount_pct BETWEEN 0 AND 100),
  starts_on DATE NOT NULL,
  ends_on DATE NOT NULL,
  active BOOLEAN GENERATED ALWAYS AS (CURRENT_DATE() BETWEEN starts_on AND ends_on) STORED
) ENGINE=InnoDB;

/* =========================
   FACTS
   ========================= */

CREATE TABLE orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT NOT NULL,
  employee_id INT NULL,
  channel_id TINYINT NOT NULL,
  order_date DATE NOT NULL,
  status ENUM('PENDING','PAID','SHIPPED','DELIVERED','CANCELLED','RETURNED') NOT NULL DEFAULT 'PENDING',
  promotion_id INT NULL,
  note VARCHAR(255) NULL,
  CONSTRAINT fk_ord_cust FOREIGN KEY (customer_id) REFERENCES customers(id),
  CONSTRAINT fk_ord_emp FOREIGN KEY (employee_id) REFERENCES employees(id),
  CONSTRAINT fk_ord_channel FOREIGN KEY (channel_id) REFERENCES channels(id),
  CONSTRAINT fk_ord_promo FOREIGN KEY (promotion_id) REFERENCES promotions(id),
  INDEX idx_orders_customer_date (customer_id, order_date),
  INDEX idx_orders_status (status)
) ENGINE=InnoDB;

CREATE TABLE order_items (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  product_id INT NOT NULL,
  qty INT NOT NULL CHECK (qty > 0),
  unit_price DECIMAL(10,2) NOT NULL CHECK (unit_price >= 0),
  discount_pct DECIMAL(5,2) NOT NULL DEFAULT 0 CHECK (discount_pct BETWEEN 0 AND 100),
  CONSTRAINT fk_oi_order FOREIGN KEY (order_id) REFERENCES orders(id),
  CONSTRAINT fk_oi_product FOREIGN KEY (product_id) REFERENCES products(id),
  INDEX idx_oi_order (order_id),
  INDEX idx_oi_product (product_id)
) ENGINE=InnoDB;

CREATE TABLE payments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  paid_at DATETIME NOT NULL,
  method ENUM('CARD','ACH','PAYPAL','CASH') NOT NULL,
  amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
  CONSTRAINT fk_pay_order FOREIGN KEY (order_id) REFERENCES orders(id),
  INDEX idx_pay_order (order_id)
) ENGINE=InnoDB;

CREATE TABLE shipments (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_id INT NOT NULL,
  shipped_at DATETIME NOT NULL,
  carrier VARCHAR(64) NOT NULL,
  tracking VARCHAR(64) UNIQUE,
  cost DECIMAL(10,2) NOT NULL CHECK (cost >= 0),
  CONSTRAINT fk_ship_order FOREIGN KEY (order_id) REFERENCES orders(id),
  INDEX idx_ship_order (order_id)
) ENGINE=InnoDB;

CREATE TABLE returns (
  id INT PRIMARY KEY AUTO_INCREMENT,
  order_item_id INT NOT NULL,
  returned_at DATETIME NOT NULL,
  reason ENUM('DAMAGED','NOT_AS_DESCRIBED','LATE','OTHER') NOT NULL,
  qty INT NOT NULL CHECK (qty > 0),
  CONSTRAINT fk_ret_oi FOREIGN KEY (order_item_id) REFERENCES order_items(id),
  INDEX idx_ret_oi (order_item_id)
) ENGINE=InnoDB;

/* =========================
   INDEXES (performance)
   ========================= */

CREATE INDEX idx_customers_region ON customers(region_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_oi_order_product ON order_items(order_id, product_id);

/* =========================
   SEED DATA
   ========================= */

INSERT INTO regions (id, name) VALUES
(1,'West'),(2,'East'),(3,'Central')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO channels (id, name) VALUES
(1,'Web'),(2,'Mobile'),(3,'Phone'),(4,'Partner')
ON DUPLICATE KEY UPDATE name=VALUES(name);

INSERT INTO categories (id, name, parent_id) VALUES
(1,'Gadgets',NULL),
(2,'Accessories',NULL),
(3,'Premium Gadgets',1),
(4,'Refurbished',NULL)
ON DUPLICATE KEY UPDATE name=VALUES(name), parent_id=VALUES(parent_id);

INSERT INTO tags (id, name) VALUES
(1,'featured'),(2,'clearance'),(3,'eco'),(4,'new')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- Employees
INSERT INTO employees (name, role, region_id, active) VALUES
('Ava Chen','AE',1,1),
('Liam Patel','AM',2,1),
('Maya Gómez','SE',3,1),
('John Smith','SUPPORT',1,1)
ON DUPLICATE KEY UPDATE role=VALUES(role), region_id=VALUES(region_id), active=VALUES(active);

-- Customers
INSERT INTO customers (name, email, region_id, created_at, vip) VALUES
('Acme Inc','contact@acme.example',1,'2024-01-10',0),
('Beta Corp',NULL,2,'2024-02-15',1),
('Cyan LLC','ops@cyan.example',1,'2024-03-03',0),
('Δelta Co','info@delta.example',3,'2024-04-20',0),
('Echo Partners','team@echo.example',2,'2024-05-05',0),
('Foxtrot AG',NULL,1,'2024-06-12',0),
('Globex','hello@globex.example',2,'2024-07-01',1),
('Initech','support@initech.example',3,'2024-07-21',0),
('Umbrella','hq@umbrella.example',1,'2024-08-09',0),
('Wayne Enterprises','contact@wayne.example',2,'2024-09-17',1)
ON DUPLICATE KEY UPDATE email=VALUES(email), region_id=VALUES(region_id), vip=VALUES(vip);

-- Products
INSERT INTO products (name, category_id, sku, price, active, created_at) VALUES
('Widget',1,'WID-001',19.99,1,'2024-01-01'),
('Gizmo',1,'GIZ-001',39.50,1,'2024-01-05'),
('Doodad',2,'DOO-001',12.00,1,'2024-02-01'),
('Widget Pro',3,'WID-PR',99.00,1,'2024-03-15'),
('Refurb Gizmo',4,'GIZ-RFB',24.99,1,'2024-04-01'),
('Eco Widget',1,'WID-ECO',29.99,1,'2024-05-10'),
('Gizmo Max',3,'GIZ-MAX',149.00,1,'2024-06-20'),
('Accessory Pack',2,'ACC-PACK',15.00,1,'2024-07-01')
ON DUPLICATE KEY UPDATE category_id=VALUES(category_id), price=VALUES(price), active=VALUES(active);

-- Product tags
INSERT INTO product_tags (product_id, tag_id) VALUES
(1,1),(2,1),(4,1),(7,1), -- featured
(5,2),(3,2),            -- clearance
(6,3),                  -- eco
(4,4),(7,4)             -- new
ON DUPLICATE KEY UPDATE tag_id=VALUES(tag_id);

-- Inventories
INSERT INTO inventories (warehouse, product_id, on_hand) VALUES
('W1',1,500),('W1',2,300),('W1',3,800),('W1',4,120),
('W2',1,200),('W2',5,150),('W2',6,400),('W2',7,100),('W2',8,600)
ON DUPLICATE KEY UPDATE on_hand=VALUES(on_hand);

-- Promotions
INSERT INTO promotions (name, discount_pct, starts_on, ends_on) VALUES
('Spring Sale',10.0,'2024-03-01','2024-03-31'),
('Summer Blast',15.0,'2024-06-01','2024-06-30'),
('Holiday',20.0,'2024-12-01','2024-12-31')
ON DUPLICATE KEY UPDATE discount_pct=VALUES(discount_pct), starts_on=VALUES(starts_on), ends_on=VALUES(ends_on);

/* =========================
   ORDERS & ITEMS (12+ months spread)
   ========================= */

-- Orders
INSERT INTO orders (customer_id, employee_id, channel_id, order_date, status, promotion_id, note) VALUES
(1, 1, 1, '2024-01-12', 'PAID', NULL, 'first order'),
(2, 2, 2, '2024-02-18', 'DELIVERED', 1, NULL),
(3, 1, 1, '2024-03-05', 'SHIPPED', 1, 'expedite'),
(4, 3, 3, '2024-03-28', 'PAID', 1, NULL),
(5, NULL, 4, '2024-04-07', 'CANCELLED', NULL, 'cancel req'),
(6, 2, 2, '2024-05-14', 'DELIVERED', NULL, NULL),
(7, 1, 1, '2024-06-09', 'DELIVERED', 2, NULL),
(8, 3, 2, '2024-07-22', 'SHIPPED', NULL, NULL),
(9, NULL, 1, '2024-08-02', 'PAID', NULL, NULL),
(10,2, 4, '2024-09-19', 'PAID', NULL, NULL),
(1, 1, 1, '2024-10-03', 'DELIVERED', NULL, 'repeat'),
(2, 2, 2, '2024-11-15', 'DELIVERED', NULL, NULL),
(3, 1, 1, '2024-12-20', 'PAID', 3, NULL),
(4, 3, 2, '2025-01-10', 'DELIVERED', NULL, NULL),
(5, NULL, 3, '2025-02-05', 'PAID', NULL, NULL),
(6, 2, 1, '2025-03-16', 'DELIVERED', NULL, NULL),
(7, 1, 4, '2025-04-08', 'PAID', NULL, NULL),
(8, 3, 2, '2025-05-21', 'SHIPPED', NULL, NULL),
(9, NULL, 1, '2025-06-02', 'DELIVERED', NULL, NULL),
(10,2, 2, '2025-07-12', 'PAID', NULL, NULL);

-- Order items
INSERT INTO order_items (order_id, product_id, qty, unit_price, discount_pct) VALUES
(1,1,2,19.99,0),(1,3,1,12.00,0),
(2,2,1,39.50,10),(2,1,3,19.99,10),
(3,4,1,99.00,10),
(4,5,2,24.99,10),
(5,2,1,39.50,0),
(6,6,3,29.99,0),(6,1,2,19.99,0),
(7,7,1,149.00,15),
(8,8,4,15.00,0),
(9,3,5,12.00,0),
(10,2,2,39.50,0),(10,4,1,99.00,0),
(11,1,5,19.99,0),
(12,2,1,39.50,0),(12,3,2,12.00,0),
(13,7,1,149.00,20),(13,1,2,19.99,20),
(14,4,1,99.00,0),
(15,8,6,15.00,0),
(16,6,2,29.99,0),(16,3,3,12.00,0),
(17,2,3,39.50,5),
(18,1,2,19.99,0),(18,5,1,24.99,0),
(19,7,1,149.00,0),
(20,6,4,29.99,0);

-- Payments
INSERT INTO payments (order_id, paid_at, method, amount) VALUES
(1,'2024-01-12 10:00:00','CARD',51.98),
(2,'2024-02-19 09:10:00','ACH',95.46),
(3,'2024-03-06 12:30:00','CARD',89.10),
(4,'2024-03-29 16:45:00','CARD',44.98),
(6,'2024-05-15 08:00:00','PAYPAL',119.96),
(7,'2024-06-10 11:22:00','CARD',126.65),
(8,'2024-07-23 14:55:00','CARD',60.00),
(9,'2024-08-02 15:20:00','CARD',60.00),
(10,'2024-09-19 09:00:00','ACH',178.00),
(11,'2024-10-03 10:00:00','CARD',99.95),
(12,'2024-11-16 10:10:00','CARD',63.50),
(13,'2024-12-20 11:11:11','CARD',151.20),
(14,'2025-01-10 12:00:00','CARD',99.00),
(15,'2025-02-05 12:30:00','PAYPAL',90.00),
(16,'2025-03-16 09:45:00','ACH',104.98),
(17,'2025-04-08 10:15:00','CARD',112.53),
(18,'2025-05-22 13:20:00','CARD',64.97),
(19,'2025-06-03 08:40:00','CARD',149.00),
(20,'2025-07-12 11:05:00','CARD',119.96);

-- Shipments
INSERT INTO shipments (order_id, shipped_at, carrier, tracking, cost) VALUES
(2,'2024-02-19 13:00:00','UPS','1Z999','12.50'),
(3,'2024-03-07 09:00:00','FedEx','FX123','15.00'),
(4,'2024-03-30 16:00:00','USPS','US777','8.25'),
(6,'2024-05-15 16:00:00','UPS','1Z100','10.00'),
(7,'2024-06-11 10:00:00','UPS','1Z101','18.00'),
(8,'2024-07-23 18:00:00','USPS','US778','6.00'),
(10,'2024-09-20 10:00:00','FedEx','FX124','20.00'),
(11,'2024-10-04 10:00:00','UPS','1Z102','9.99'),
(12,'2024-11-17 09:00:00','USPS','US779','7.50'),
(14,'2025-01-10 15:30:00','UPS','1Z103','9.00'),
(16,'2025-03-17 11:00:00','UPS','1Z104','10.50'),
(18,'2025-05-22 19:00:00','USPS','US780','6.75'),
(19,'2025-06-04 08:00:00','FedEx','FX125','22.00')
ON DUPLICATE KEY UPDATE carrier=VALUES(carrier), tracking=VALUES(tracking), cost=VALUES(cost);

-- Returns
INSERT INTO returns (order_item_id, returned_at, reason, qty) VALUES
(2,'2024-02-25 10:00:00','NOT_AS_DESCRIBED',1),
(13,'2024-11-25 12:00:00','DAMAGED',1),
(21,'2025-02-10 09:00:00','OTHER',2)
ON DUPLICATE KEY UPDATE reason=VALUES(reason), qty=VALUES(qty);

/* =========================
   VIEWS
   ========================= */

CREATE OR REPLACE VIEW v_product_revenue AS
SELECT
  p.id AS product_id,
  p.name AS product_name,
  SUM( (oi.qty * oi.unit_price) * (1 - oi.discount_pct/100) ) AS gross_revenue
FROM order_items oi
JOIN products p ON p.id = oi.product_id
JOIN orders o ON o.id = oi.order_id
WHERE o.status NOT IN ('CANCELLED')
GROUP BY 1,2;

CREATE OR REPLACE VIEW v_monthly_sales AS
SELECT
  DATE_FORMAT(o.order_date, '%Y-%m') AS ym,
  SUM( (oi.qty * oi.unit_price) * (1 - oi.discount_pct/100) ) AS gross_revenue,
  COUNT(DISTINCT o.id) AS orders_count
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.status NOT IN ('CANCELLED')
GROUP BY 1
ORDER BY 1;

CREATE OR REPLACE VIEW v_customer_ltv AS
SELECT
  c.id AS customer_id,
  c.name AS customer_name,
  SUM(p.amount) AS total_paid,
  COUNT(DISTINCT o.id) AS orders_count,
  MIN(o.order_date) AS first_order,
  MAX(o.order_date) AS last_order
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.status NOT IN ('CANCELLED')
LEFT JOIN payments p ON p.order_id = o.id
GROUP BY 1,2;

/* =========================
   HELPER FUNCTION
   ========================= */

DROP FUNCTION IF EXISTS fiscal_quarter;
DELIMITER $$
CREATE FUNCTION fiscal_quarter(d DATE) RETURNS VARCHAR(7)
DETERMINISTIC
BEGIN
  DECLARE m INT;
  DECLARE y INT;
  SET m = MONTH(d);
  SET y = YEAR(d);
  IF m BETWEEN 4 AND 6 THEN RETURN CONCAT('FY', y, ' Q1');
  ELSEIF m BETWEEN 7 AND 9 THEN RETURN CONCAT('FY', y, ' Q2');
  ELSEIF m BETWEEN 10 AND 12 THEN RETURN CONCAT('FY', y, ' Q3');
  ELSE RETURN CONCAT('FY', y-1, ' Q4');
  END IF;
END$$
DELIMITER ;
