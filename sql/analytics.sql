-- Top customers by revenue
SELECT c.customer_id, c.customer_name, ROUND(SUM(f.revenue),2) AS revenue
FROM fact_sales f JOIN dim_customer c USING(customer_key)
GROUP BY c.customer_id, c.customer_name ORDER BY revenue DESC;

-- Category contribution
SELECT p.category, ROUND(SUM(f.revenue),2) AS revenue
FROM fact_sales f JOIN dim_product p USING(product_key)
GROUP BY p.category ORDER BY revenue DESC;
