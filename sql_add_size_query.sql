query = '''
                                                                START TRANSACTION;

                                                                INSERT INTO `olegsent_wp8`.`wp_posts` (`post_author`, `post_title`,
                                                                            `comment_status`, `ping_status`, `post_name`,`post_parent`,
                                                                            `guid`,`post_type`, `post_status`)
                                                                VALUES ('53', '#',
                                                                        'closed', 'closed','1','{0}', '1', 'product_variation', 'publish' );

                                                                SET @postsid:= @@IDENTITY;


                            									INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_regular_price', '{1}');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_sale_price', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_sale_price_dates_from', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_sale_price_dates_to', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_price', '{1}');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, 'attribute_pa_size', '{2}');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_stock_status', 'instock');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_sku', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_thumbnail_id', '0');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_virtual', 'no');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_downloadable', 'no');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_weight', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_length', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_width', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_height', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_manage_stock', 'no');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_download_limit', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_download_expiry', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_downloadable_files', '');

                                                                INSERT INTO `olegsent_wp8`.`wp_postmeta` (`post_id`, `meta_key`, `meta_value`)
                                                                VALUES (@postsid, '_variation_description', '');
                                                                COMMIT;
                                                                '''.format(bm_drs[3], bm_drs[2], size)