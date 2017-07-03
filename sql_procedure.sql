DELIMITER $$
CREATE DEFINER=`root`@`%` PROCEDURE `get_product_attributes`(IN `ProductName` TEXT)
BEGIN
SELECT DISTINCT
     p.post_title AS 'Product Name',
     t.name AS 'Term Name',
     tt.taxonomy AS 'Term Type',
     tt.description AS 'Term Description'
FROM
     wp_posts AS p
INNER JOIN
     wp_term_relationships AS tr ON p.id = tr.object_id
INNER JOIN
     wp_term_taxonomy AS tt ON tt.term_taxonomy_id = tr.term_taxonomy_id
INNER JOIN
     wp_terms AS t ON t.term_id = tt.term_id
WHERE
     p.post_title= ProductName
AND
     p.post_type = 'product';
END$$
DELIMITER ;