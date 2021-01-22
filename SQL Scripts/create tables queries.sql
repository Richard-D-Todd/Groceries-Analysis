DROP TABLE order_details, delivered_items, unavailable_items;
CREATE TABLE order_details
(
	order_number VARCHAR PRIMARY KEY,
	delivery_date DATE NOT NULL,
	subtotal NUMERIC(5, 2),
	total NUMERIC(5, 2)
);

CREATE TABLE delivered_items
(
	id serial PRIMARY KEY,
	order_number VARCHAR REFERENCES order_details(order_number),
	item VARCHAR NOT NULL,
	substitution BOOL NOT NULL,
	substituting VARCHAR,
	price NUMERIC(5, 2),
	quantity SMALLINT,
	unit_price NUMERIC(5, 2)
);

CREATE TABLE unavailable_items
(
    id serial PRIMARY Key,
    order_number VARCHAR REFERENCES order_details(order_number),
    item VARCHAR NOT NULL,
    quantity SMALLINT
);    

CREATE TABLE email_datetime 
(
	order_number VARCHAR PRIMARY KEY,
	received_datetime DATE NOT NULL,
);